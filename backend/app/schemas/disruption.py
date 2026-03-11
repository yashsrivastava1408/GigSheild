from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import DisruptionEventType


class DisruptionEventCreateRequest(BaseModel):
    event_type: DisruptionEventType
    zone_id: str = Field(min_length=2, max_length=64)
    severity: int = Field(ge=1, le=4)
    started_at: datetime
    ended_at: datetime | None = None
    weather_api_raw: dict | None = None
    verified: bool = True


class DisruptionEventResponse(BaseModel):
    id: str
    event_type: DisruptionEventType
    zone_id: str
    severity: int
    started_at: datetime
    ended_at: datetime | None
    weather_api_raw: dict | None
    verified: bool

    model_config = {"from_attributes": True}
