import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.fraud_log import FraudLog
from app.models.enums import ClaimStatus, PayoutStatus, RoutingDecision
from app.models.payout import Payout
from app.repositories.claims import (
    create_claim,
    get_claim_by_event_and_worker,
    list_claims_for_worker,
    update_claim,
)
from app.repositories.disruptions import get_disruption_event_by_id
from app.repositories.fraud_logs import create_fraud_log
from app.repositories.payouts import list_payouts_for_worker
from app.repositories.policies import list_active_policies_for_zone
from app.schemas.claim import AutoClaimCreateResponse
from app.services.plausibility import create_plausibility_record, evaluate_claim_plausibility
from app.services.payments import issue_claim_payout
from app.services.trust import recompute_trust_score
from app.services.workers import require_worker


SEVERITY_MULTIPLIER = {
    1: Decimal("0.25"),
    2: Decimal("0.50"),
    3: Decimal("0.75"),
    4: Decimal("1.00"),
}

ROUTING_TO_CLAIM_STATUS = {
    RoutingDecision.approve: ClaimStatus.auto_approved,
    RoutingDecision.manual_review: ClaimStatus.manual_review,
    RoutingDecision.reject: ClaimStatus.rejected,
}


def create_automatic_claims(db: Session, disruption_event_id: str) -> AutoClaimCreateResponse:
    event = get_disruption_event_by_id(db, disruption_event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disruption event not found.")

    active_policies = list_active_policies_for_zone(db, event.zone_id)
    auto_approved = 0
    manual_review = 0
    auto_rejected = 0
    total_payout_initiated = Decimal("0.00")

    for policy in active_policies:
        if get_claim_by_event_and_worker(db, policy.worker_id, event.id) is not None:
            continue

        payout_amount = (Decimal(str(policy.coverage_amount)) * SEVERITY_MULTIPLIER[event.severity]).quantize(
            Decimal("0.01")
        )
        trust_score = float(policy.worker.trust_score)
        evaluation = evaluate_claim_plausibility(
            db,
            worker=policy.worker,
            policy=policy,
            disruption_event=event,
            claim_amount=float(payout_amount),
            trust_score=trust_score,
        )
        claim_status = ROUTING_TO_CLAIM_STATUS[evaluation.routing_decision]
        fraud_score = Decimal(str(100 - evaluation.plausibility_score))
        claim_id = str(uuid.uuid4())

        claim = create_claim(
            db,
            Claim(
                id=claim_id,
                policy_id=policy.id,
                worker_id=policy.worker_id,
                disruption_event_id=event.id,
                amount=float(payout_amount),
                status=claim_status,
                fraud_score=float(fraud_score),
                trust_score_at_claim=trust_score,
            ),
        )
        create_plausibility_record(db, claim_id=claim.id, evaluation=evaluation)
        create_fraud_log(
            db,
            FraudLog(
                id=str(uuid.uuid4()),
                worker_id=claim.worker_id,
                claim_id=claim.id,
                fraud_type="automated_claim_assessment",
                fraud_score=float(fraud_score),
                signals={"plausibility_score": evaluation.plausibility_score, "signals": [signal.model_dump() for signal in evaluation.signals]},
                action_taken=claim_status,
            ),
        )
        worker = require_worker(db, claim.worker_id)

        if claim_status == ClaimStatus.auto_approved:
            auto_approved += 1
            payout = issue_claim_payout(db, worker, claim, float(payout_amount))
            if payout.status in {PayoutStatus.completed, PayoutStatus.processing, PayoutStatus.pending}:
                total_payout_initiated += payout_amount
        elif claim_status == ClaimStatus.manual_review:
            manual_review += 1
        else:
            auto_rejected += 1
        recompute_trust_score(db, worker)

    return AutoClaimCreateResponse(
        disruption_event_id=event.id,
        affected_zone=event.zone_id,
        workers_affected=len(active_policies),
        auto_approved=auto_approved,
        manual_review=manual_review,
        auto_rejected=auto_rejected,
        total_payout_initiated=float(total_payout_initiated),
    )


def get_worker_claims(db: Session, worker_id: str) -> list[Claim]:
    return list_claims_for_worker(db, worker_id)


def get_worker_payouts(db: Session, worker_id: str) -> list[Payout]:
    return list_payouts_for_worker(db, worker_id)


def approve_manual_claim(db: Session, claim: Claim):
    claim.status = ClaimStatus.auto_approved
    updated_claim = update_claim(db, claim)
    payout = issue_claim_payout(db, require_worker(db, updated_claim.worker_id), updated_claim, float(updated_claim.amount))
    if payout.status == PayoutStatus.completed:
        updated_claim.status = ClaimStatus.paid
        update_claim(db, updated_claim)
    recompute_trust_score(db, require_worker(db, updated_claim.worker_id))
    return payout


def reject_manual_claim(db: Session, claim: Claim) -> Claim:
    claim.status = ClaimStatus.rejected
    updated_claim = update_claim(db, claim)
    recompute_trust_score(db, require_worker(db, updated_claim.worker_id))
    return updated_claim
