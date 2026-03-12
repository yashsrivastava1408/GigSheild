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
ADMIN_HEADERS = {"x-admin-key": "dev-admin-key"}


def _register_worker(phone: str, name: str, zone_id: str, tenure_days: int, *, kyc_verified: bool = True) -> str:
    app.dependency_overrides[get_db] = override_get_db
    response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": phone,
            "name": name,
            "platform": "swiggy",
            "zone_id": zone_id,
            "avg_weekly_earnings": 3200,
            "tenure_days": tenure_days,
            "kyc_verified": kyc_verified,
        },
    )
    return response.json()["id"]


def _create_policy(worker_id: str, tier: str) -> None:
    app.dependency_overrides[get_db] = override_get_db
    client.post("/api/v1/policies", json={"worker_id": worker_id, "coverage_tier": tier})


def _create_event(zone_id: str, severity: int) -> str:
    app.dependency_overrides[get_db] = override_get_db
    response = client.post(
        "/api/v1/disruptions",
        json={
            "event_type": "heavy_rain",
            "zone_id": zone_id,
            "severity": severity,
            "started_at": (datetime.now(UTC) - timedelta(minutes=30)).isoformat(),
            "verified": True,
            "weather_api_raw": {"source": "test"},
        },
    )
    return response.json()["id"]


def test_auth_otp_login_and_me_endpoint() -> None:
    app.dependency_overrides[get_db] = override_get_db
    _register_worker("9012345678", "Ravi", "chennai_zone_4", 200)

    otp_response = client.post("/api/v1/auth/request-otp", json={"phone": "9012345678"})
    assert otp_response.status_code == 200
    otp_code = otp_response.json()["mock_otp_code"]

    verify_response = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone": "9012345678", "otp_code": otp_code},
    )
    assert verify_response.status_code == 200
    token = verify_response.json()["access_token"]

    me_response = client.get("/api/v1/workers/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["phone"] == "9012345678"


def test_manual_review_admin_approval_and_fraud_feed() -> None:
    app.dependency_overrides[get_db] = override_get_db
    worker_id = _register_worker("9023456781", "Aman", "mumbai_zone_2", 5, kyc_verified=False)
    _create_policy(worker_id, "basic")
    event_id = _create_event("mumbai_zone_2", 2)

    auto_response = client.post("/api/v1/claims/auto-create", json={"disruption_event_id": event_id})
    assert auto_response.status_code == 200
    assert auto_response.json()["manual_review"] == 1

    admin_claims = client.get("/api/v1/admin/claims", headers=ADMIN_HEADERS)
    assert admin_claims.status_code == 200
    claim_id = admin_claims.json()[0]["id"]

    approve_response = client.post(f"/api/v1/admin/claims/{claim_id}/approve", headers=ADMIN_HEADERS)
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "completed"

    fraud_logs = client.get("/api/v1/admin/fraud-logs", headers=ADMIN_HEADERS)
    assert fraud_logs.status_code == 200
    assert len(fraud_logs.json()) >= 1


def test_weather_sync_and_policy_expiry_internal_endpoints() -> None:
    app.dependency_overrides[get_db] = override_get_db
    sync_response = client.post("/api/v1/internal/weather/sync", headers=ADMIN_HEADERS)
    assert sync_response.status_code == 200

    expire_response = client.post("/api/v1/internal/policies/expire", headers=ADMIN_HEADERS)
    assert expire_response.status_code == 200
    assert "expired_policies" in expire_response.json()
