from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payout import Payout


def create_payout(db: Session, payout: Payout) -> Payout:
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


def list_payouts_for_worker(db: Session, worker_id: str) -> list[Payout]:
    statement = select(Payout).where(Payout.worker_id == worker_id).order_by(Payout.processed_at.desc())
    return list(db.scalars(statement))
