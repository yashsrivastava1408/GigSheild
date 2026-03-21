from datetime import datetime

from pydantic import BaseModel

from app.models.enums import RiskTier, RoutingDecision, SignalImpact


class PlausibilitySignal(BaseModel):
    code: str
    description: str
    impact: SignalImpact
    weight: int
    evidence: str


class PlausibilityAssessmentResponse(BaseModel):
    id: str
    claim_id: str
    plausibility_score: int
    risk_tier: RiskTier
    routing_decision: RoutingDecision
    signals: list[PlausibilitySignal]
    assessed_at: datetime

    model_config = {"from_attributes": True}
