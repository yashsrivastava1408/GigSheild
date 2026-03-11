from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.disruption_event import DisruptionEvent
from app.models.enums import DisruptionEventType


def create_disruption_event(db: Session, event: DisruptionEvent) -> DisruptionEvent:
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_disruption_event_by_id(db: Session, event_id: str) -> DisruptionEvent | None:
    return db.get(DisruptionEvent, event_id)


def list_active_disruptions(db: Session, as_of: datetime | None = None) -> list[DisruptionEvent]:
    moment = as_of or datetime.now(UTC)
    statement = select(DisruptionEvent).where(
        DisruptionEvent.started_at <= moment,
        (DisruptionEvent.ended_at.is_(None)) | (DisruptionEvent.ended_at >= moment),
    )
    return list(db.scalars(statement.order_by(DisruptionEvent.started_at.desc())))


def get_matching_active_event(
    db: Session,
    zone_id: str,
    event_type: DisruptionEventType,
    as_of: datetime | None = None,
) -> DisruptionEvent | None:
    moment = as_of or datetime.now(UTC)
    statement = select(DisruptionEvent).where(
        DisruptionEvent.zone_id == zone_id,
        DisruptionEvent.event_type == event_type,
        DisruptionEvent.started_at <= moment,
        (DisruptionEvent.ended_at.is_(None)) | (DisruptionEvent.ended_at >= moment),
    )
    return db.scalar(statement)
