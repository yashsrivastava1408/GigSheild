from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.enums import ClaimStatus, PayoutProfileStatus
from app.repositories.claims import get_claim_by_id, list_manual_review_claims, update_claim
from app.repositories.fraud_logs import list_fraud_logs
from app.repositories.plausibility_assessments import list_plausibility_assessments
from app.repositories.workers import list_workers_by_payout_status, update_worker
from app.services.claims import approve_manual_claim, reject_manual_claim
from app.services.workers import require_worker


def get_manual_review_claims(db: Session):
    return list_manual_review_claims(db)


def approve_claim(db: Session, claim_id: str):
    claim = get_claim_by_id(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
    if claim.status != ClaimStatus.manual_review:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Claim is not pending manual review.")
    return approve_manual_claim(db, claim)


def reject_claim(db: Session, claim_id: str):
    claim = get_claim_by_id(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
    if claim.status != ClaimStatus.manual_review:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Claim is not pending manual review.")
    return reject_manual_claim(db, claim)


def get_fraud_log_feed(db: Session):
    return list_fraud_logs(db)


def get_plausibility_feed(db: Session):
    return list_plausibility_assessments(db)


def get_payout_profile_feed(db: Session):
    return list_workers_by_payout_status(db, PayoutProfileStatus.pending)


def approve_payout_profile(db: Session, worker_id: str, notes: str | None):
    worker = require_worker(db, worker_id)
    worker.payout_profile_status = PayoutProfileStatus.verified
    worker.payout_profile_review_notes = notes
    worker.payout_profile_reviewed_at = utcnow()
    return update_worker(db, worker)


def reject_payout_profile(db: Session, worker_id: str, notes: str | None):
    worker = require_worker(db, worker_id)
    worker.payout_profile_status = PayoutProfileStatus.rejected
    worker.payout_profile_review_notes = notes
    worker.payout_profile_reviewed_at = utcnow()
    return update_worker(db, worker)
