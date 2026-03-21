from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.schemas.admin import AdminPayoutProfileResponse, FraudLogResponse, PlausibilityAssessmentResponse
from app.schemas.claim import ClaimResponse
from app.schemas.payout import PayoutResponse
from app.schemas.worker import AdminPayoutProfileReviewRequest
from app.services.admin import (
    approve_claim,
    approve_payout_profile,
    get_fraud_log_feed,
    get_manual_review_claims,
    get_payout_profile_feed,
    get_plausibility_feed,
    reject_claim,
    reject_payout_profile,
)


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


@router.get("/plausibility-assessments", response_model=list[PlausibilityAssessmentResponse])
async def list_admin_plausibility_assessments(db: Session = Depends(get_db)) -> list[PlausibilityAssessmentResponse]:
    return [PlausibilityAssessmentResponse.model_validate(assessment) for assessment in get_plausibility_feed(db)]


@router.get("/payout-profiles", response_model=list[AdminPayoutProfileResponse])
async def list_admin_payout_profiles(db: Session = Depends(get_db)) -> list[AdminPayoutProfileResponse]:
    return [AdminPayoutProfileResponse.model_validate(worker) for worker in get_payout_profile_feed(db)]


@router.post("/payout-profiles/{worker_id}/approve", response_model=AdminPayoutProfileResponse)
async def approve_admin_payout_profile(
    worker_id: str,
    payload: AdminPayoutProfileReviewRequest,
    db: Session = Depends(get_db),
) -> AdminPayoutProfileResponse:
    return AdminPayoutProfileResponse.model_validate(approve_payout_profile(db, worker_id, payload.notes))


@router.post("/payout-profiles/{worker_id}/reject", response_model=AdminPayoutProfileResponse)
async def reject_admin_payout_profile(
    worker_id: str,
    payload: AdminPayoutProfileReviewRequest,
    db: Session = Depends(get_db),
) -> AdminPayoutProfileResponse:
    return AdminPayoutProfileResponse.model_validate(reject_payout_profile(db, worker_id, payload.notes))
