from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import Platform


class WorkerCreateRequest(BaseModel):
    phone: str = Field(pattern=r"^\d{10}$")
    name: str = Field(min_length=2, max_length=100)
    platform: Platform
    zone_id: str = Field(min_length=2, max_length=64)
    avg_weekly_earnings: float = Field(gt=0)
    tenure_days: int = Field(ge=0, default=0)
    kyc_verified: bool = False


class WorkerResponse(BaseModel):
    id: str
    phone: str
    name: str
    platform: Platform
    zone_id: str
    trust_score: float
    avg_weekly_earnings: float
    tenure_days: int
    kyc_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}
