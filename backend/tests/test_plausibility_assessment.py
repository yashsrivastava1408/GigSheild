from collections.abc import Generator
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


settings.use_mock_payouts = True


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
Base.metadata.create_all(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _admin_headers() -> dict[str, str]:
    response = client.post("/api/v1/auth/admin/login", json={"admin_key": "dev-admin-key"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_plausibility_assessment_is_persisted_and_routes_manual_review() -> None:
    worker_response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": "9444412345",
            "name": "Nikhil",
            "platform": "swiggy",
            "zone_id": "chennai_zone_4",
            "avg_weekly_earnings": 3100,
            "tenure_days": 12,
            "kyc_verified": False,
        },
    )
    worker_id = worker_response.json()["id"]

    client.post(
        "/api/v1/policies",
        json={"worker_id": worker_id, "coverage_tier": "standard"},
    )

    event_response = client.post(
        "/api/v1/disruptions",
        json={
            "event_type": "heavy_rain",
            "zone_id": "chennai_zone_4",
            "severity": 2,
            "started_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "verified": True,
            "weather_api_raw": {"rainfall_mm_per_hr": 18},
        },
    )

    auto_claim_response = client.post("/api/v1/claims/auto-create", json={"disruption_event_id": event_response.json()["id"]})
    assert auto_claim_response.status_code == 200
    assert auto_claim_response.json()["manual_review"] == 1

    claims_response = client.get("/api/v1/claims", params={"worker_id": worker_id})
    assert claims_response.status_code == 200
    claim_id = claims_response.json()[0]["id"]

    assessments_response = client.get("/api/v1/admin/plausibility-assessments", headers=_admin_headers())
    assert assessments_response.status_code == 200
    assessments = assessments_response.json()
    assessment = next(item for item in assessments if item["claim_id"] == claim_id)
    assert assessment["plausibility_score"] == 50
    assert assessment["risk_tier"] == "medium"
    assert assessment["routing_decision"] == "manual_review"

    signal_codes = {signal["code"] for signal in assessment["signals"]}
    assert {"POLICY_TOO_NEW", "EARLY_LIFECYCLE", "ZONE_HISTORY_MATCH", "AMOUNT_OK", "VERIFIED_TRIGGER", "WEATHER_MATCH", "LOW_PEER_DENSITY"} <= signal_codes
