from pydantic import BaseModel, Field

from app.models.enums import CoverageTier, Platform


class PremiumQuoteQuery(BaseModel):
    coverage_tier: CoverageTier
    platform: Platform
    city: str = Field(min_length=2, max_length=80)
    zone_id: str = Field(min_length=2, max_length=64)
    avg_weekly_earnings: float = Field(gt=0)
    tenure_days: int = Field(ge=0)
    trust_score: float = Field(ge=0, le=100)


class PremiumQuoteResponse(BaseModel):
    coverage_tier: CoverageTier
    weekly_premium: float
    coverage_amount: float
    risk_score: float
    risk_multiplier: float
    valid_from: str
    valid_to: str
    triggers: list[str]
    quote_factors: dict[str, float | str]
