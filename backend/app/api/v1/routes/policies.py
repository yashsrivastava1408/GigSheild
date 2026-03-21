from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.policies import get_policy_by_id, list_policies_for_worker
from app.schemas.policy import (
    PolicyCheckoutRequest,
    PolicyCheckoutResponse,
    PolicyPurchaseWithPaymentRequest,
    PolicyResponse,
)
from app.services.payments import create_policy_checkout_order, encode_checkout_notes, record_policy_checkout
from app.services.policies import build_policy_quote, purchase_policy
from app.services.workers import require_worker


router = APIRouter()


@router.post("/checkout", response_model=PolicyCheckoutResponse)
async def create_policy_checkout(
    payload: PolicyCheckoutRequest,
    db: Session = Depends(get_db),
) -> PolicyCheckoutResponse:
    worker = require_worker(db, payload.worker_id)
    quote = build_policy_quote(worker, payload.coverage_tier)
    order = create_policy_checkout_order(payload, quote)
    record_policy_checkout(db, payload, order, quote)
    return PolicyCheckoutResponse(
        **order,
        worker_id=payload.worker_id,
        coverage_tier=payload.coverage_tier,
        notes_token=encode_checkout_notes(payload.worker_id, payload.coverage_tier.value),
    )


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyPurchaseWithPaymentRequest,
    db: Session = Depends(get_db),
) -> PolicyResponse:
    worker = require_worker(db, payload.worker_id)
    policy, risk_score, risk_multiplier = purchase_policy(db, payload, payload.payment)
    quote = build_policy_quote(worker, payload.coverage_tier)
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
    quote = build_policy_quote(worker, policy.coverage_tier)
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
        quote = build_policy_quote(worker, policy.coverage_tier)
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
