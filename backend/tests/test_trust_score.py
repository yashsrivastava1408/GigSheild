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
from app.services.trust import compute_trust_score


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


def test_compute_trust_score_blends_positive_and_negative_signals() -> None:
    trust_score = compute_trust_score(
        kyc_verified=True,
        tenure_days=240,
        policy_count=3,
        approved_claim_count=2,
        manual_review_count=1,
        rejected_claim_count=0,
        confirmed_fraud_count=0,
        has_recent_adverse_event=False,
    )

    assert trust_score == 91.0


def test_worker_registration_uses_profile_based_trust_score() -> None:
    response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": "9000011111",
            "name": "Meera",
            "platform": "swiggy",
            "zone_id": "chennai_zone_4",
            "avg_weekly_earnings": 3400,
            "tenure_days": 200,
            "kyc_verified": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["trust_score"] == 85.0


def test_manual_review_claim_recomputes_trust_score() -> None:
    worker_response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": "9000011112",
            "name": "Arjun",
            "platform": "swiggy",
            "zone_id": "pune_zone_1",
            "avg_weekly_earnings": 3200,
            "tenure_days": 15,
            "kyc_verified": False,
        },
    )
    worker_id = worker_response.json()["id"]
    assert worker_response.json()["trust_score"] == 60.0

    client.post("/api/v1/policies", json={"worker_id": worker_id, "coverage_tier": "basic"})

    event_response = client.post(
        "/api/v1/disruptions",
        json={
            "event_type": "heavy_rain",
            "zone_id": "pune_zone_1",
            "severity": 2,
            "started_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "verified": True,
            "weather_api_raw": {"rainfall_mm_per_hr": 20},
        },
    )

    auto_claim_response = client.post(
        "/api/v1/claims/auto-create",
        json={"disruption_event_id": event_response.json()["id"]},
    )
    assert auto_claim_response.status_code == 200
    assert auto_claim_response.json()["manual_review"] == 1

    worker_profile = client.get(f"/api/v1/workers/{worker_id}")
    assert worker_profile.status_code == 200
    assert worker_profile.json()["trust_score"] == 55.0
