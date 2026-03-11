from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.schemas.disruption import DisruptionEventResponse
from app.services.scheduler import expire_policies
from app.services.weather_sync import sync_weather_events


router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/weather/sync", response_model=list[DisruptionEventResponse])
async def sync_weather(db: Session = Depends(get_db)) -> list[DisruptionEventResponse]:
    return [DisruptionEventResponse.model_validate(event) for event in sync_weather_events(db)]


@router.post("/policies/expire")
async def expire_old_policies(db: Session = Depends(get_db)) -> dict[str, int]:
    return {"expired_policies": expire_policies(db)}
