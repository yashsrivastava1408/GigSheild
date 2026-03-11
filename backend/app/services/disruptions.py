import uuid

from sqlalchemy.orm import Session

from app.models.disruption_event import DisruptionEvent
from app.repositories.disruptions import create_disruption_event, list_active_disruptions
from app.schemas.disruption import DisruptionEventCreateRequest


def create_event(db: Session, payload: DisruptionEventCreateRequest) -> DisruptionEvent:
    event = DisruptionEvent(
        id=str(uuid.uuid4()),
        event_type=payload.event_type,
        zone_id=payload.zone_id,
        severity=payload.severity,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        weather_api_raw=payload.weather_api_raw,
        verified=payload.verified,
    )
    return create_disruption_event(db, event)


def get_active_events(db: Session) -> list[DisruptionEvent]:
    return list_active_disruptions(db)
