import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.worker import Worker
from app.repositories.workers import create_worker, get_worker_by_id, get_worker_by_phone
from app.schemas.worker import WorkerCreateRequest
from app.services.trust import compute_initial_trust_score


def register_worker(db: Session, payload: WorkerCreateRequest) -> Worker:
    existing = get_worker_by_phone(db, payload.phone)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker with this phone number already exists.",
        )

    worker = Worker(
        id=str(uuid.uuid4()),
        phone=payload.phone,
        name=payload.name,
        platform=payload.platform,
        zone_id=payload.zone_id,
        avg_weekly_earnings=payload.avg_weekly_earnings,
        tenure_days=payload.tenure_days,
        kyc_verified=payload.kyc_verified,
        trust_score=compute_initial_trust_score(payload.kyc_verified, payload.tenure_days),
    )
    return create_worker(db, worker)


def require_worker(db: Session, worker_id: str) -> Worker:
    worker = get_worker_by_id(db, worker_id)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    return worker
