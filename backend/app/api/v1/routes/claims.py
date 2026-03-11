from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.claim import AutoClaimCreateRequest, AutoClaimCreateResponse, ClaimResponse
from app.schemas.payout import PayoutResponse
from app.services.claims import create_automatic_claims, get_worker_claims, get_worker_payouts
from app.services.workers import require_worker


router = APIRouter()


@router.get("", response_model=list[ClaimResponse])
async def list_worker_claims(worker_id: str, db: Session = Depends(get_db)) -> list[ClaimResponse]:
    require_worker(db, worker_id)
    return [ClaimResponse.model_validate(claim) for claim in get_worker_claims(db, worker_id)]


@router.get("/payouts", response_model=list[PayoutResponse])
async def list_worker_payouts(worker_id: str, db: Session = Depends(get_db)) -> list[PayoutResponse]:
    require_worker(db, worker_id)
    return [PayoutResponse.model_validate(payout) for payout in get_worker_payouts(db, worker_id)]


@router.post("/auto-create", response_model=AutoClaimCreateResponse)
async def auto_create_claims(
    payload: AutoClaimCreateRequest,
    db: Session = Depends(get_db),
) -> AutoClaimCreateResponse:
    return create_automatic_claims(db, payload.disruption_event_id)
