import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import PolicyStatus
from app.models.policy import Policy
from app.repositories.policies import create_policy, get_active_policy_for_worker
from app.schemas.policy import PolicyPurchaseRequest
from app.schemas.premium import PremiumQuoteQuery
from app.services.premium import build_quote_response
from app.services.trust import recompute_trust_score
from app.services.workers import require_worker


def purchase_policy(db: Session, payload: PolicyPurchaseRequest) -> tuple[Policy, float, float]:
    worker = require_worker(db, payload.worker_id)
    existing_policy = get_active_policy_for_worker(db, worker.id, date.today())
    if existing_policy is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker already has an active policy for the current coverage window.",
        )

    quote = build_quote_response(
        PremiumQuoteQuery(
            coverage_tier=payload.coverage_tier,
            platform=worker.platform,
            city=worker.zone_id.split("_")[0],
            zone_id=worker.zone_id,
            avg_weekly_earnings=float(worker.avg_weekly_earnings),
            tenure_days=worker.tenure_days,
            trust_score=float(worker.trust_score),
        )
    )

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
    recompute_trust_score(db, worker)
    return created_policy, quote.risk_score, quote.risk_multiplier
