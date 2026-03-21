import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import PolicyStatus
from app.models.policy import Policy
from app.models.worker_zone_observation import WorkerZoneObservation
from app.repositories.policies import create_policy, get_active_policy_for_worker
from app.repositories.worker_zone_observations import create_worker_zone_observation
from app.schemas.policy import PolicyPurchaseRequest
from app.schemas.premium import PremiumQuoteQuery
from app.services.payments import attach_payment_to_policy, verify_policy_payment
from app.services.premium import build_quote_response
from app.services.trust import recompute_trust_score
from app.services.workers import require_worker


def build_policy_quote(worker, coverage_tier):
    return build_quote_response(
        PremiumQuoteQuery(
            coverage_tier=coverage_tier,
            platform=worker.platform,
            city=worker.zone_id.split("_")[0],
            zone_id=worker.zone_id,
            avg_weekly_earnings=float(worker.avg_weekly_earnings),
            tenure_days=worker.tenure_days,
            trust_score=float(worker.trust_score),
        )
    )


def purchase_policy(db: Session, payload: PolicyPurchaseRequest, payment=None) -> tuple[Policy, float, float]:
    worker = require_worker(db, payload.worker_id)
    existing_policy = get_active_policy_for_worker(db, worker.id, date.today())
    if existing_policy is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker already has an active policy for the current coverage window.",
        )

    quote = build_policy_quote(worker, payload.coverage_tier)
    payment_record = verify_policy_payment(db, payment)

    start_date = date.today()
    policy = Policy(
        id=str(uuid.uuid4()),
        worker_id=worker.id,
        coverage_tier=payload.coverage_tier,
        weekly_premium=quote.weekly_premium,
        coverage_amount=quote.coverage_amount,
        start_date=start_date,
        end_date=start_date + timedelta(days=6),
        status=PolicyStatus.active,
    )
    created_policy = create_policy(db, policy)
    create_worker_zone_observation(
        db,
        WorkerZoneObservation(
            id=str(uuid.uuid4()),
            worker_id=worker.id,
            zone_id=worker.zone_id,
            source="policy_purchase",
        ),
    )
    recompute_trust_score(db, worker)
    attach_payment_to_policy(db, payment_record, created_policy.id)
    return created_policy, quote.risk_score, quote.risk_multiplier
