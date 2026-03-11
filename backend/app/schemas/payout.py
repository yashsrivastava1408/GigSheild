from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PaymentMethod, PayoutStatus


class PayoutResponse(BaseModel):
    id: str
    claim_id: str
    worker_id: str
    amount: float
    payment_method: PaymentMethod
    razorpay_payment_id: str
    status: PayoutStatus
    processed_at: datetime

    model_config = {"from_attributes": True}
