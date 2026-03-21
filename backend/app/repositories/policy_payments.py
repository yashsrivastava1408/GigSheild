from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy_payment import PolicyPayment


def create_policy_payment(db: Session, payment: PolicyPayment) -> PolicyPayment:
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_policy_payment_by_order_id(db: Session, razorpay_order_id: str) -> PolicyPayment | None:
    return db.scalar(select(PolicyPayment).where(PolicyPayment.razorpay_order_id == razorpay_order_id))


def get_policy_payment_by_payment_id(db: Session, razorpay_payment_id: str) -> PolicyPayment | None:
    return db.scalar(select(PolicyPayment).where(PolicyPayment.razorpay_payment_id == razorpay_payment_id))


def update_policy_payment(db: Session, payment: PolicyPayment) -> PolicyPayment:
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
