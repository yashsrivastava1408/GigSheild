from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ClaimStatus


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
