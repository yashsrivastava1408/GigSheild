from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.enums import ClaimStatus


def create_claim(db: Session, claim: Claim) -> Claim:
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def list_claims_for_worker(db: Session, worker_id: str) -> list[Claim]:
    statement = select(Claim).where(Claim.worker_id == worker_id).order_by(Claim.created_at.desc())
    return list(db.scalars(statement))


def get_claim_by_event_and_worker(db: Session, worker_id: str, disruption_event_id: str) -> Claim | None:
    statement = select(Claim).where(
        Claim.worker_id == worker_id,
        Claim.disruption_event_id == disruption_event_id,
    )
    return db.scalar(statement)


def count_claims_for_event_since(db: Session, disruption_event_id: str, since: datetime) -> int:
    statement = select(func.count()).select_from(Claim).where(
        Claim.disruption_event_id == disruption_event_id,
        Claim.created_at >= since,
    )
    return int(db.scalar(statement) or 0)


def list_recent_claims_for_worker(db: Session, worker_id: str, since: datetime) -> list[Claim]:
    statement = (
        select(Claim)
        .where(Claim.worker_id == worker_id, Claim.created_at >= since)
        .order_by(Claim.created_at.desc())
    )
    return list(db.scalars(statement))


def get_claim_by_id(db: Session, claim_id: str) -> Claim | None:
    return db.get(Claim, claim_id)


def list_manual_review_claims(db: Session) -> list[Claim]:
    statement = select(Claim).where(Claim.status == ClaimStatus.manual_review).order_by(Claim.created_at.desc())
    return list(db.scalars(statement))


def update_claim(db: Session, claim: Claim) -> Claim:
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim
