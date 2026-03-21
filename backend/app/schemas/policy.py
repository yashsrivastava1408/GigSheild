from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import CoverageTier, PolicyStatus


class PolicyPurchaseRequest(BaseModel):
    worker_id: str
    coverage_tier: CoverageTier


class PolicyPurchaseVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PolicyCheckoutRequest(BaseModel):
    worker_id: str
    coverage_tier: CoverageTier


class PolicyCheckoutResponse(BaseModel):
    checkout_required: bool
    key_id: str
    order_id: str
    amount: int
    currency: str
    worker_id: str
    coverage_tier: CoverageTier
    notes_token: str


class PolicyPurchaseWithPaymentRequest(PolicyPurchaseRequest):
    payment: PolicyPurchaseVerification | None = None


class PolicyResponse(BaseModel):
    id: str
    worker_id: str
    coverage_tier: CoverageTier
    weekly_premium: float
    coverage_amount: float
    start_date: date
    end_date: date
    status: PolicyStatus
    created_at: datetime
    triggers: list[str] = Field(default_factory=list)
    risk_score: float | None = None
    risk_multiplier: float | None = None

    model_config = {"from_attributes": True}
