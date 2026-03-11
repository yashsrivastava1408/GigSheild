from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PolicyStatus
from app.models.policy import Policy


def create_policy(db: Session, policy: Policy) -> Policy:
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def update_policy(db: Session, policy: Policy) -> Policy:
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_policy_by_id(db: Session, policy_id: str) -> Policy | None:
    return db.get(Policy, policy_id)


def list_policies_for_worker(db: Session, worker_id: str) -> list[Policy]:
    return list(
        db.scalars(
            select(Policy).where(Policy.worker_id == worker_id).order_by(Policy.created_at.desc())
        )
    )


def get_active_policy_for_worker(db: Session, worker_id: str, as_of: date) -> Policy | None:
    statement = select(Policy).where(
        Policy.worker_id == worker_id,
        Policy.status == PolicyStatus.active,
        Policy.start_date <= as_of,
        Policy.end_date >= as_of,
    )
    return db.scalar(statement)


def list_active_policies_for_zone(db: Session, zone_id: str, as_of: date | None = None) -> list[Policy]:
    target_date = as_of or date.today()
    statement = (
        select(Policy)
        .join(Policy.worker)
        .where(
            Policy.status == PolicyStatus.active,
            Policy.start_date <= target_date,
            Policy.end_date >= target_date,
            Policy.worker.has(zone_id=zone_id),
        )
    )
    return list(db.scalars(statement))


def list_expired_active_policies(db: Session, as_of: date) -> list[Policy]:
    statement = select(Policy).where(Policy.status == PolicyStatus.active, Policy.end_date < as_of)
    return list(db.scalars(statement))
