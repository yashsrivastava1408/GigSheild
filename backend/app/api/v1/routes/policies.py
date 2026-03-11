from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.policies import get_policy_by_id, list_policies_for_worker
from app.schemas.policy import PolicyPurchaseRequest, PolicyResponse
from app.schemas.premium import PremiumQuoteQuery
from app.services.policies import purchase_policy
from app.services.premium import build_quote_response
from app.services.workers import require_worker


router = APIRouter()


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyPurchaseRequest,
    db: Session = Depends(get_db),
) -> PolicyResponse:
    worker = require_worker(db, payload.worker_id)
    policy, risk_score, risk_multiplier = purchase_policy(db, payload)
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
    response = PolicyResponse.model_validate(policy)
    return response.model_copy(
        update={
            "triggers": quote.triggers,
            "risk_score": risk_score,
            "risk_multiplier": risk_multiplier,
        }
    )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str, db: Session = Depends(get_db)) -> PolicyResponse:
    policy = get_policy_by_id(db, policy_id)
    if policy is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Policy not found.")

    worker = require_worker(db, policy.worker_id)
    quote = build_quote_response(
        PremiumQuoteQuery(
            coverage_tier=policy.coverage_tier,
            platform=worker.platform,
            city=worker.zone_id.split("_")[0],
            zone_id=worker.zone_id,
            avg_weekly_earnings=float(worker.avg_weekly_earnings),
            tenure_days=worker.tenure_days,
            trust_score=float(worker.trust_score),
        )
    )
    response = PolicyResponse.model_validate(policy)
    return response.model_copy(
        update={
            "triggers": quote.triggers,
            "risk_score": quote.risk_score,
            "risk_multiplier": quote.risk_multiplier,
        }
    )


@router.get("", response_model=list[PolicyResponse])
async def get_worker_policies(worker_id: str, db: Session = Depends(get_db)) -> list[PolicyResponse]:
    worker = require_worker(db, worker_id)
    policies = list_policies_for_worker(db, worker.id)
    responses: list[PolicyResponse] = []
    for policy in policies:
        quote = build_quote_response(
            PremiumQuoteQuery(
                coverage_tier=policy.coverage_tier,
                platform=worker.platform,
                city=worker.zone_id.split("_")[0],
                zone_id=worker.zone_id,
                avg_weekly_earnings=float(worker.avg_weekly_earnings),
                tenure_days=worker.tenure_days,
                trust_score=float(worker.trust_score),
            )
        )
        response = PolicyResponse.model_validate(policy)
        responses.append(
            response.model_copy(
                update={
                    "triggers": quote.triggers,
                    "risk_score": quote.risk_score,
                    "risk_multiplier": quote.risk_multiplier,
                }
            )
        )
    return responses
