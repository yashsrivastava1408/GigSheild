from dataclasses import dataclass
from datetime import date, timedelta

from app.models.enums import CoverageTier, Platform
from app.schemas.premium import PremiumQuoteQuery, PremiumQuoteResponse


CITY_RISK_INDEX = {
    "chennai": 0.82,
    "mumbai": 0.78,
    "bengaluru": 0.52,
    "delhi": 0.71,
}

TIER_CONFIG = {
    CoverageTier.basic: {
        "coverage_amount": 400.0,
        "triggers": ["rainfall > 15mm/hr", "flood_level_2+"],
    },
    CoverageTier.standard: {
        "coverage_amount": 800.0,
        "triggers": ["rainfall > 15mm/hr", "temp > 43C", "flood_level_2+", "aqi > 400"],
    },
    CoverageTier.premium: {
        "coverage_amount": 1500.0,
        "triggers": [
            "rainfall > 15mm/hr",
            "temp > 43C",
            "flood_level_2+",
            "aqi > 400",
            "curfew_notification",
            "platform_outage > 2h",
        ],
    },
}

PLATFORM_FACTOR = {
    Platform.zomato: 0.00,
    Platform.swiggy: 0.03,
    Platform.zepto: 0.07,
    Platform.blinkit: 0.05,
}


@dataclass(frozen=True)
class QuoteComputation:
    risk_score: float
    risk_multiplier: float
    weekly_premium: float


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def compute_risk_score(query: PremiumQuoteQuery) -> float:
    city_risk = CITY_RISK_INDEX.get(query.city.strip().lower(), 0.60)
    earnings_factor = _bounded(query.avg_weekly_earnings / 4500, 0.35, 1.15)
    tenure_factor = _bounded(1 - (query.tenure_days / 730), 0.15, 1.0)
    trust_factor = _bounded(1 - (query.trust_score / 100), 0.05, 1.0)
    platform_factor = PLATFORM_FACTOR[query.platform]

    risk_score = (
        city_risk * 0.35
        + earnings_factor * 0.20
        + tenure_factor * 0.20
        + trust_factor * 0.20
        + platform_factor * 0.05
    )
    return round(_bounded(risk_score, 0.05, 0.99), 2)


def calculate_quote(query: PremiumQuoteQuery) -> QuoteComputation:
    coverage_amount = TIER_CONFIG[query.coverage_tier]["coverage_amount"]
    base_premium = coverage_amount * 0.015
    risk_score = compute_risk_score(query)
    risk_multiplier = round(0.5 + (risk_score * 1.5), 2)
    weekly_premium = round(_bounded(base_premium * risk_multiplier, 29.0, 89.0), 2)
    return QuoteComputation(
        risk_score=risk_score,
        risk_multiplier=risk_multiplier,
        weekly_premium=weekly_premium,
    )


def build_quote_response(query: PremiumQuoteQuery) -> PremiumQuoteResponse:
    quote = calculate_quote(query)
    tier_config = TIER_CONFIG[query.coverage_tier]
    valid_from = date.today()
    valid_to = valid_from + timedelta(days=6)

    return PremiumQuoteResponse(
        coverage_tier=query.coverage_tier,
        weekly_premium=quote.weekly_premium,
        coverage_amount=tier_config["coverage_amount"],
        risk_score=quote.risk_score,
        risk_multiplier=quote.risk_multiplier,
        valid_from=valid_from.isoformat(),
        valid_to=valid_to.isoformat(),
        triggers=tier_config["triggers"],
        quote_factors={
            "city": query.city,
            "zone_id": query.zone_id,
            "platform": query.platform.value,
            "avg_weekly_earnings": query.avg_weekly_earnings,
            "tenure_days": float(query.tenure_days),
            "trust_score": query.trust_score,
        },
    )
