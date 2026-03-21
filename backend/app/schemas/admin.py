from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ClaimStatus, PaymentMethod, PayoutProfileStatus, RiskTier, RoutingDecision
from app.schemas.plausibility import PlausibilitySignal


class FraudLogResponse(BaseModel):
    id: str
    worker_id: str
    claim_id: str
    fraud_type: str
    fraud_score: float
    signals: dict
    action_taken: ClaimStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PlausibilityAssessmentResponse(BaseModel):
    id: str
    claim_id: str
    plausibility_score: int
    risk_tier: RiskTier
    routing_decision: RoutingDecision
    signals: list[PlausibilitySignal]
    assessed_at: datetime

    model_config = {"from_attributes": True}


class AdminPayoutProfileResponse(BaseModel):
    id: str
    name: str
    phone: str
    payout_method: PaymentMethod | None
    payout_upi_id: str | None
    payout_bank_account_name: str | None
    payout_bank_account_number: str | None
    payout_bank_ifsc: str | None
    payout_contact_name: str | None
    payout_contact_phone: str | None
    payout_profile_status: PayoutProfileStatus
    payout_profile_review_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
