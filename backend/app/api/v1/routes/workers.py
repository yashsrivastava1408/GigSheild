from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_worker
from app.db.session import get_db
from app.schemas.worker import WorkerCreateRequest, WorkerPayoutProfileUpdateRequest, WorkerResponse
from app.services.workers import register_worker, require_worker, update_worker_payout_profile


router = APIRouter()


@router.post("/register", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
async def create_worker_account(
    payload: WorkerCreateRequest,
    db: Session = Depends(get_db),
) -> WorkerResponse:
    worker = register_worker(db, payload)
    return WorkerResponse.model_validate(worker)


@router.get("/me", response_model=WorkerResponse)
async def get_current_worker_profile(worker=Depends(get_current_worker)) -> WorkerResponse:
    return WorkerResponse.model_validate(worker)


@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: str, db: Session = Depends(get_db)) -> WorkerResponse:
    worker = require_worker(db, worker_id)
    return WorkerResponse.model_validate(worker)


@router.patch("/me/payout-profile", response_model=WorkerResponse)
async def save_payout_profile(
    payload: WorkerPayoutProfileUpdateRequest,
    current_worker=Depends(get_current_worker),
    db: Session = Depends(get_db),
) -> WorkerResponse:
    worker = update_worker_payout_profile(db, current_worker.id, payload)
    return WorkerResponse.model_validate(worker)
