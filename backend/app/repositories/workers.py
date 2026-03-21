from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PayoutProfileStatus
from app.models.worker import Worker


def get_worker_by_id(db: Session, worker_id: str) -> Worker | None:
    return db.get(Worker, worker_id)


def get_worker_by_phone(db: Session, phone: str) -> Worker | None:
    return db.scalar(select(Worker).where(Worker.phone == phone))


def create_worker(db: Session, worker: Worker) -> Worker:
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


def update_worker(db: Session, worker: Worker) -> Worker:
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


def list_workers_by_device_fingerprint(db: Session, device_fingerprint: str) -> list[Worker]:
    statement = select(Worker).where(Worker.device_fingerprint == device_fingerprint)
    return list(db.scalars(statement))


def list_distinct_worker_zone_ids(db: Session) -> list[str]:
    statement = select(Worker.zone_id).distinct().order_by(Worker.zone_id.asc())
    return [row[0] for row in db.execute(statement).all()]


def list_workers_by_payout_status(db: Session, payout_status: PayoutProfileStatus) -> list[Worker]:
    statement = (
        select(Worker)
        .where(Worker.payout_profile_status == payout_status)
        .order_by(Worker.created_at.desc())
    )
    return list(db.scalars(statement))
