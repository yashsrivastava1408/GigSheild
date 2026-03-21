from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import ensure_utc
from app.core.time import utcnow
from app.models.worker_zone_observation import WorkerZoneObservation


def create_worker_zone_observation(db: Session, observation: WorkerZoneObservation) -> WorkerZoneObservation:
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


def list_recent_worker_zone_observations(
    db: Session,
    worker_id: str,
    since: datetime | None = None,
) -> list[WorkerZoneObservation]:
    cutoff = ensure_utc(since) if since is not None else utcnow() - timedelta(days=30)
    statement = (
        select(WorkerZoneObservation)
        .where(WorkerZoneObservation.worker_id == worker_id, WorkerZoneObservation.observed_at >= cutoff)
        .order_by(WorkerZoneObservation.observed_at.desc())
    )
    return list(db.scalars(statement))


def list_worker_zone_observations(db: Session, worker_id: str) -> list[WorkerZoneObservation]:
    statement = select(WorkerZoneObservation).where(WorkerZoneObservation.worker_id == worker_id)
    return list(db.scalars(statement))
