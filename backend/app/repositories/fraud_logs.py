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
