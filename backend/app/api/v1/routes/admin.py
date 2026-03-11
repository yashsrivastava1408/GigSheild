from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.schemas.admin import FraudLogResponse
from app.schemas.claim import ClaimResponse
from app.schemas.payout import PayoutResponse
from app.services.admin import approve_claim, get_fraud_log_feed, get_manual_review_claims, reject_claim


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/claims", response_model=list[ClaimResponse])
async def list_admin_claims(db: Session = Depends(get_db)) -> list[ClaimResponse]:
    return [ClaimResponse.model_validate(claim) for claim in get_manual_review_claims(db)]


@router.post("/claims/{claim_id}/approve", response_model=PayoutResponse)
async def approve_admin_claim(claim_id: str, db: Session = Depends(get_db)) -> PayoutResponse:
    return PayoutResponse.model_validate(approve_claim(db, claim_id))


@router.post("/claims/{claim_id}/reject", response_model=ClaimResponse)
async def reject_admin_claim(claim_id: str, db: Session = Depends(get_db)) -> ClaimResponse:
    return ClaimResponse.model_validate(reject_claim(db, claim_id))


@router.get("/fraud-logs", response_model=list[FraudLogResponse])
async def list_admin_fraud_logs(db: Session = Depends(get_db)) -> list[FraudLogResponse]:
    return [FraudLogResponse.model_validate(log) for log in get_fraud_log_feed(db)]
