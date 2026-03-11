from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_premium_quote_endpoint_returns_quote() -> None:
    response = client.get(
        "/api/v1/premium/quote",
        params={
            "coverage_tier": "standard",
            "platform": "swiggy",
            "city": "Chennai",
            "zone_id": "chennai_zone_4",
            "avg_weekly_earnings": 3800,
            "tenure_days": 365,
            "trust_score": 82,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["coverage_tier"] == "standard"
    assert payload["coverage_amount"] == 800.0
    assert payload["weekly_premium"] >= 29.0
    assert payload["weekly_premium"] <= 89.0
    assert "rainfall > 15mm/hr" in payload["triggers"]


def test_premium_quote_requires_valid_platform() -> None:
    response = client.get(
        "/api/v1/premium/quote",
        params={
            "coverage_tier": "basic",
            "platform": "uber",
            "city": "Mumbai",
            "zone_id": "mumbai_zone_2",
            "avg_weekly_earnings": 2500,
            "tenure_days": 90,
            "trust_score": 75,
        },
    )

    assert response.status_code == 422
