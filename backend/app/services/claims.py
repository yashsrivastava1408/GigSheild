import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.fraud_log import FraudLog
from app.models.enums import ClaimStatus, PaymentMethod, PayoutStatus
from app.models.payout import Payout
from app.repositories.claims import (
    create_claim,
    get_claim_by_event_and_worker,
    list_claims_for_worker,
    update_claim,
)
from app.repositories.disruptions import get_disruption_event_by_id
from app.repositories.fraud_logs import create_fraud_log
from app.repositories.payouts import create_payout, list_payouts_for_worker
from app.repositories.policies import list_active_policies_for_zone
from app.schemas.claim import AutoClaimCreateResponse
from app.services.providers import issue_mock_payout_reference
from app.services.trust import recompute_trust_score
from app.services.workers import require_worker


SEVERITY_MULTIPLIER = {
    1: Decimal("0.25"),
    2: Decimal("0.50"),
    3: Decimal("0.75"),
    4: Decimal("1.00"),
}


def _claim_decision(trust_score: Decimal) -> tuple[ClaimStatus, Decimal]:
    if trust_score >= Decimal("75"):
        return ClaimStatus.auto_approved, Decimal("18.00")
    if trust_score >= Decimal("50"):
        return ClaimStatus.manual_review, Decimal("42.00")
    return ClaimStatus.rejected, Decimal("81.00")


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

        trust_score = Decimal(str(policy.worker.trust_score))
        claim_status, fraud_score = _claim_decision(trust_score)
        payout_amount = (Decimal(str(policy.coverage_amount)) * SEVERITY_MULTIPLIER[event.severity]).quantize(
            Decimal("0.01")
        )

        claim = create_claim(
            db,
            Claim(
                id=str(uuid.uuid4()),
                policy_id=policy.id,
                worker_id=policy.worker_id,
                disruption_event_id=event.id,
                amount=float(payout_amount),
                status=claim_status,
                fraud_score=float(fraud_score),
                trust_score_at_claim=float(trust_score),
            ),
        )
        create_fraud_log(
            db,
            FraudLog(
                id=str(uuid.uuid4()),
                worker_id=claim.worker_id,
                claim_id=claim.id,
                fraud_type="automated_claim_assessment",
                fraud_score=float(fraud_score),
                signals={"trust_score": float(trust_score), "event_severity": event.severity},
                action_taken=claim_status,
            ),
        )
        worker = require_worker(db, claim.worker_id)

        if claim_status == ClaimStatus.auto_approved:
            auto_approved += 1
            create_payout(
                db,
                Payout(
                    id=str(uuid.uuid4()),
                    claim_id=claim.id,
                    worker_id=claim.worker_id,
                    amount=float(payout_amount),
                    payment_method=PaymentMethod.upi,
                    razorpay_payment_id=issue_mock_payout_reference(claim.id),
                    status=PayoutStatus.completed,
                ),
            )
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


def approve_manual_claim(db: Session, claim: Claim) -> Payout:
    claim.status = ClaimStatus.paid
    updated_claim = update_claim(db, claim)
    payout = create_payout(
        db,
        Payout(
            id=str(uuid.uuid4()),
            claim_id=updated_claim.id,
            worker_id=updated_claim.worker_id,
            amount=float(updated_claim.amount),
            payment_method=PaymentMethod.upi,
            razorpay_payment_id=issue_mock_payout_reference(updated_claim.id),
            status=PayoutStatus.completed,
        ),
    )
    recompute_trust_score(db, require_worker(db, updated_claim.worker_id))
    return payout


def reject_manual_claim(db: Session, claim: Claim) -> Claim:
    claim.status = ClaimStatus.rejected
    updated_claim = update_claim(db, claim)
    recompute_trust_score(db, require_worker(db, updated_claim.worker_id))
    return updated_claim
