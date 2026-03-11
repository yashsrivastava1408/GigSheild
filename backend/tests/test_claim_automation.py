from collections.abc import Generator
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


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


def test_auto_claim_creation_generates_claims_and_payouts() -> None:
    worker_response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": "9988776655",
            "name": "Vikram",
            "platform": "zomato",
            "zone_id": "chennai_zone_4",
            "avg_weekly_earnings": 3900,
            "tenure_days": 300,
            "kyc_verified": True,
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
            "severity": 3,
            "started_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "verified": True,
            "weather_api_raw": {"rainfall_mm_per_hr": 18},
        },
    )
    event_id = event_response.json()["id"]

    auto_claim_response = client.post("/api/v1/claims/auto-create", json={"disruption_event_id": event_id})
    assert auto_claim_response.status_code == 200
    summary = auto_claim_response.json()
    assert summary["workers_affected"] == 1
    assert summary["auto_approved"] == 1
    assert summary["total_payout_initiated"] == 600.0

    claims_response = client.get("/api/v1/claims", params={"worker_id": worker_id})
    assert claims_response.status_code == 200
    claims = claims_response.json()
    assert len(claims) == 1
    assert claims[0]["status"] == "auto_approved"
    assert claims[0]["amount"] == 600.0

    payouts_response = client.get("/api/v1/claims/payouts", params={"worker_id": worker_id})
    assert payouts_response.status_code == 200
    payouts = payouts_response.json()
    assert len(payouts) == 1
    assert payouts[0]["status"] == "completed"
    assert payouts[0]["amount"] == 600.0
