from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fraud_log import FraudLog


def create_fraud_log(db: Session, fraud_log: FraudLog) -> FraudLog:
    db.add(fraud_log)
    db.commit()
    db.refresh(fraud_log)
    return fraud_log


def list_fraud_logs(db: Session) -> list[FraudLog]:
    return list(db.scalars(select(FraudLog).order_by(FraudLog.created_at.desc())))


def list_fraud_logs_for_worker(db: Session, worker_id: str) -> list[FraudLog]:
    statement = select(FraudLog).where(FraudLog.worker_id == worker_id).order_by(FraudLog.created_at.desc())
    return list(db.scalars(statement))
