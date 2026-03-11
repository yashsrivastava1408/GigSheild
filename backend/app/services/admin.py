from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import ClaimStatus
from app.repositories.claims import get_claim_by_id, list_manual_review_claims, update_claim
from app.repositories.fraud_logs import list_fraud_logs
from app.services.claims import approve_manual_claim, reject_manual_claim


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
