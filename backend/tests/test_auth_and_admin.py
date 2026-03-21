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


def _create_event(zone_id: str, severity: int, *, weather_api_raw: dict | None = None) -> str:
    app.dependency_overrides[get_db] = override_get_db
    response = client.post(
        "/api/v1/disruptions",
        json={
            "event_type": "heavy_rain",
            "zone_id": zone_id,
            "severity": severity,
            "started_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "verified": True,
            "weather_api_raw": weather_api_raw or {"source": "test"},
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
    event_id = _create_event("mumbai_zone_2", 2, weather_api_raw={"source": "test", "rainfall_mm_per_hr": 18})

    auto_response = client.post("/api/v1/claims/auto-create", json={"disruption_event_id": event_id})
    assert auto_response.status_code == 200
    assert auto_response.json()["manual_review"] == 1

    admin_claims = client.get("/api/v1/admin/claims", headers=_admin_headers())
    assert admin_claims.status_code == 200
    claim_id = admin_claims.json()[0]["id"]

    approve_response = client.post(f"/api/v1/admin/claims/{claim_id}/approve", headers=_admin_headers())
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "completed"

    fraud_logs = client.get("/api/v1/admin/fraud-logs", headers=_admin_headers())
    assert fraud_logs.status_code == 200
    assert len(fraud_logs.json()) >= 1


def test_weather_sync_and_policy_expiry_internal_endpoints() -> None:
    app.dependency_overrides[get_db] = override_get_db
    sync_response = client.post("/api/v1/internal/weather/sync", headers=_admin_headers())
    assert sync_response.status_code == 200

    expire_response = client.post("/api/v1/internal/policies/expire", headers=_admin_headers())
    assert expire_response.status_code == 200
    assert "expired_policies" in expire_response.json()


def test_payout_profile_submission_and_admin_review() -> None:
    worker_id = _register_worker("9034567891", "Nisha", "delhi_zone_7", 120)

    otp_response = client.post("/api/v1/auth/request-otp", json={"phone": "9034567891"})
    token = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone": "9034567891", "otp_code": otp_response.json()["mock_otp_code"]},
    ).json()["access_token"]

    profile_response = client.patch(
        "/api/v1/workers/me/payout-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "payout_method": "upi",
            "payout_upi_id": "nisha@upi",
            "payout_contact_name": "Nisha",
            "payout_contact_phone": "9034567891",
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["payout_profile_status"] == "pending"

    payout_profiles = client.get("/api/v1/admin/payout-profiles", headers=_admin_headers())
    assert payout_profiles.status_code == 200
    assert payout_profiles.json()[0]["id"] == worker_id

    approve_response = client.post(
        f"/api/v1/admin/payout-profiles/{worker_id}/approve",
        headers=_admin_headers(),
        json={"notes": "Verified"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["payout_profile_status"] == "verified"


def test_full_demo_loop_from_quote_to_completed_payout() -> None:
    app.dependency_overrides[get_db] = override_get_db
    worker_id = _register_worker("9045678912", "Karan", "chennai_zone_4", 240)

    otp_response = client.post("/api/v1/auth/request-otp", json={"phone": "9045678912"})
    assert otp_response.status_code == 200
    token = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone": "9045678912", "otp_code": otp_response.json()["mock_otp_code"]},
    ).json()["access_token"]

    quote_response = client.get(
        "/api/v1/premium/quote",
        params={
            "coverage_tier": "standard",
            "platform": "swiggy",
            "city": "Chennai",
            "zone_id": "chennai_zone_4",
            "avg_weekly_earnings": 3200,
            "tenure_days": 240,
            "trust_score": 60,
        },
    )
    assert quote_response.status_code == 200
    assert quote_response.json()["weekly_premium"] > 0

    checkout_response = client.post(
        "/api/v1/policies/checkout",
        json={"worker_id": worker_id, "coverage_tier": "standard"},
    )
    assert checkout_response.status_code == 200
    assert checkout_response.json()["checkout_required"] is False

    profile_response = client.patch(
        "/api/v1/workers/me/payout-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "payout_method": "upi",
            "payout_upi_id": "karan@upi",
            "payout_contact_name": "Karan",
            "payout_contact_phone": "9045678912",
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["payout_profile_status"] == "pending"

    approve_profile_response = client.post(
        f"/api/v1/admin/payout-profiles/{worker_id}/approve",
        headers=_admin_headers(),
        json={"notes": "Demo-ready profile"},
    )
    assert approve_profile_response.status_code == 200
    assert approve_profile_response.json()["payout_profile_status"] == "verified"

    policy_response = client.post(
        "/api/v1/policies",
        json={"worker_id": worker_id, "coverage_tier": "standard"},
    )
    assert policy_response.status_code == 201

    event_id = _create_event("chennai_zone_4", 3, weather_api_raw={"source": "test", "rainfall_mm_per_hr": 22})
    auto_response = client.post("/api/v1/claims/auto-create", json={"disruption_event_id": event_id})
    assert auto_response.status_code == 200
    body = auto_response.json()
    assert body["workers_affected"] == 1
    assert body["auto_approved"] == 1
    assert body["manual_review"] == 0

    claims_response = client.get("/api/v1/claims", params={"worker_id": worker_id})
    assert claims_response.status_code == 200
    claims = claims_response.json()
    assert len(claims) == 1
    assert claims[0]["status"] == "auto_approved"

    payouts_response = client.get("/api/v1/claims/payouts", params={"worker_id": worker_id})
    assert payouts_response.status_code == 200
    payouts = payouts_response.json()
    assert len(payouts) == 1
    assert payouts[0]["status"] == "completed"
