from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.disruption import DisruptionEventCreateRequest, DisruptionEventResponse
from app.services.disruptions import create_event, get_active_events


router = APIRouter()


@router.get("/active", response_model=list[DisruptionEventResponse])
async def list_active_disruptions(db: Session = Depends(get_db)) -> list[DisruptionEventResponse]:
    return [DisruptionEventResponse.model_validate(event) for event in get_active_events(db)]


@router.post("", response_model=DisruptionEventResponse, status_code=status.HTTP_201_CREATED)
async def create_disruption(
    payload: DisruptionEventCreateRequest,
    db: Session = Depends(get_db),
) -> DisruptionEventResponse:
    event = create_event(db, payload)
    return DisruptionEventResponse.model_validate(event)
