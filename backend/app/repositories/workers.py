from sqlalchemy import select
from sqlalchemy.orm import Session

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
