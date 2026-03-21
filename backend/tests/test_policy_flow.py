from collections.abc import Generator

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


def test_worker_registration_and_policy_purchase_flow() -> None:
    register_response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": "9876543210",
            "name": "Ravi Kumar",
            "platform": "zomato",
            "zone_id": "chennai_zone_4",
            "avg_weekly_earnings": 3600,
            "tenure_days": 210,
            "kyc_verified": True,
        },
    )
    assert register_response.status_code == 201
    worker = register_response.json()

    policy_response = client.post(
        "/api/v1/policies",
        json={
            "worker_id": worker["id"],
            "coverage_tier": "standard",
        },
    )
    assert policy_response.status_code == 201
    policy = policy_response.json()
    assert policy["worker_id"] == worker["id"]
    assert policy["coverage_tier"] == "standard"
    assert policy["coverage_amount"] == 800.0
    assert policy["status"] == "active"
    assert "rainfall > 15mm/hr" in policy["triggers"]


def test_duplicate_active_policy_is_rejected() -> None:
    register_response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": "9123456789",
            "name": "Asha",
            "platform": "swiggy",
            "zone_id": "mumbai_zone_2",
            "avg_weekly_earnings": 4100,
            "tenure_days": 400,
            "kyc_verified": True,
        },
    )
    worker_id = register_response.json()["id"]

    first_policy = client.post(
        "/api/v1/policies",
        json={"worker_id": worker_id, "coverage_tier": "basic"},
    )
    assert first_policy.status_code == 201

    duplicate_policy = client.post(
        "/api/v1/policies",
        json={"worker_id": worker_id, "coverage_tier": "premium"},
    )
    assert duplicate_policy.status_code == 409


def test_policy_checkout_endpoint_returns_mock_mode_payload() -> None:
    register_response = client.post(
        "/api/v1/workers/register",
        json={
            "phone": "9234567890",
            "name": "Leela",
            "platform": "zepto",
            "zone_id": "delhi_zone_7",
            "avg_weekly_earnings": 4300,
            "tenure_days": 180,
            "kyc_verified": True,
        },
    )
    worker_id = register_response.json()["id"]

    checkout_response = client.post(
        "/api/v1/policies/checkout",
        json={"worker_id": worker_id, "coverage_tier": "basic"},
    )
    assert checkout_response.status_code == 200
    body = checkout_response.json()
    assert body["currency"] == "INR"
    assert body["amount"] > 0
