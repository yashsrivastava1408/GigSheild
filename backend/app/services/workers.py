import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.worker import Worker
from app.models.worker_zone_observation import WorkerZoneObservation
from app.models.enums import PayoutProfileStatus
from app.repositories.workers import create_worker, get_worker_by_id, get_worker_by_phone, update_worker
from app.schemas.worker import WorkerCreateRequest, WorkerPayoutProfileUpdateRequest
from app.repositories.worker_zone_observations import create_worker_zone_observation
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
        device_fingerprint=payload.device_fingerprint,
        avg_weekly_earnings=payload.avg_weekly_earnings,
        tenure_days=payload.tenure_days,
        kyc_verified=payload.kyc_verified,
        trust_score=compute_initial_trust_score(payload.kyc_verified, payload.tenure_days),
        payout_profile_status=PayoutProfileStatus.missing,
    )
    created_worker = create_worker(db, worker)
    create_worker_zone_observation(
        db,
        WorkerZoneObservation(
            id=str(uuid.uuid4()),
            worker_id=created_worker.id,
            zone_id=created_worker.zone_id,
            source="registration",
        ),
    )
    return created_worker


def require_worker(db: Session, worker_id: str) -> Worker:
    worker = get_worker_by_id(db, worker_id)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    return worker


def update_worker_payout_profile(db: Session, worker_id: str, payload: WorkerPayoutProfileUpdateRequest) -> Worker:
    worker = require_worker(db, worker_id)
    worker.payout_method = payload.payout_method
    worker.payout_upi_id = payload.payout_upi_id
    worker.payout_bank_account_name = payload.payout_bank_account_name
    worker.payout_bank_account_number = payload.payout_bank_account_number
    worker.payout_bank_ifsc = payload.payout_bank_ifsc
    worker.payout_contact_name = payload.payout_contact_name
    worker.payout_contact_phone = payload.payout_contact_phone
    worker.payout_fund_account_id = None
    worker.payout_profile_status = PayoutProfileStatus.pending
    worker.payout_profile_review_notes = None
    worker.payout_profile_reviewed_at = None
    return update_worker(db, worker)
