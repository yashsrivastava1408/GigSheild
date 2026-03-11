from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ClaimStatus


class ClaimResponse(BaseModel):
    id: str
    policy_id: str
    worker_id: str
    disruption_event_id: str
    amount: float
    status: ClaimStatus
    fraud_score: float
    trust_score_at_claim: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AutoClaimCreateRequest(BaseModel):
    disruption_event_id: str


class AutoClaimCreateResponse(BaseModel):
    disruption_event_id: str
    affected_zone: str
    workers_affected: int
    auto_approved: int
    manual_review: int
    auto_rejected: int
    total_payout_initiated: float
