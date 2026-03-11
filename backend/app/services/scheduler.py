from datetime import date

from sqlalchemy.orm import Session

from app.models.enums import PolicyStatus
from app.repositories.policies import list_expired_active_policies, update_policy


def expire_policies(db: Session, as_of: date | None = None) -> int:
    target_date = as_of or date.today()
    policies = list_expired_active_policies(db, target_date)
    for policy in policies:
        policy.status = PolicyStatus.expired
        update_policy(db, policy)
    return len(policies)
