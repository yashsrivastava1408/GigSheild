from fastapi import APIRouter, Query

from app.models.enums import CoverageTier, Platform
from app.schemas.premium import PremiumQuoteQuery, PremiumQuoteResponse
from app.services.premium import build_quote_response


router = APIRouter()


@router.get("/quote", response_model=PremiumQuoteResponse)
async def get_premium_quote(
    coverage_tier: CoverageTier,
    platform: Platform,
    city: str = Query(min_length=2, max_length=80),
    zone_id: str = Query(min_length=2, max_length=64),
    avg_weekly_earnings: float = Query(gt=0),
    tenure_days: int = Query(ge=0),
    trust_score: float = Query(ge=0, le=100),
) -> PremiumQuoteResponse:
    query = PremiumQuoteQuery(
        coverage_tier=coverage_tier,
        platform=platform,
        city=city,
        zone_id=zone_id,
        avg_weekly_earnings=avg_weekly_earnings,
        tenure_days=tenure_days,
        trust_score=trust_score,
    )
    return build_quote_response(query)
