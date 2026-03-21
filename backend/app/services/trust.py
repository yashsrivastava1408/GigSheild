from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import ensure_utc
from app.core.time import utcnow
from app.models.enums import ClaimStatus
from app.models.worker import Worker
from app.repositories.claims import list_claims_for_worker
from app.repositories.fraud_logs import list_fraud_logs_for_worker
from app.repositories.policies import list_policies_for_worker
from app.repositories.workers import update_worker


BASE_TRUST_SCORE = 60.0
KYC_VERIFIED_BONUS = 15.0
RECOVERY_BONUS = 2.0
CLAIM_APPROVAL_BONUS = 3.0
CLAIM_APPROVAL_BONUS_CAP = 12.0
MANUAL_REVIEW_PENALTY = 5.0
MANUAL_REVIEW_PENALTY_CAP = 10.0
CLAIM_REJECTION_PENALTY = 8.0
CLAIM_REJECTION_PENALTY_CAP = 24.0
CONFIRMED_FRAUD_PENALTY = 20.0
CONFIRMED_FRAUD_PENALTY_CAP = 40.0


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _tenure_bonus(tenure_days: int) -> float:
    if tenure_days >= 180:
        return 10.0
    if tenure_days >= 90:
        return 5.0
    if tenure_days >= 30:
        return 2.0
    return 0.0


def _renewal_bonus(policy_count: int) -> float:
    if policy_count >= 4:
        return 5.0
    if policy_count >= 2:
        return 3.0
    return 0.0


def compute_initial_trust_score(kyc_verified: bool, tenure_days: int) -> float:
    score = BASE_TRUST_SCORE + _tenure_bonus(tenure_days)
    if kyc_verified:
        score += KYC_VERIFIED_BONUS
    return round(_bounded(score, 0.0, 100.0), 2)


def compute_trust_score(
    *,
    kyc_verified: bool,
    tenure_days: int,
    policy_count: int,
    approved_claim_count: int,
    manual_review_count: int,
    rejected_claim_count: int,
    confirmed_fraud_count: int,
    has_recent_adverse_event: bool,
) -> float:
    score = compute_initial_trust_score(kyc_verified, tenure_days)
    score += _renewal_bonus(policy_count)
    score += min(approved_claim_count * CLAIM_APPROVAL_BONUS, CLAIM_APPROVAL_BONUS_CAP)
    score -= min(manual_review_count * MANUAL_REVIEW_PENALTY, MANUAL_REVIEW_PENALTY_CAP)
    score -= min(rejected_claim_count * CLAIM_REJECTION_PENALTY, CLAIM_REJECTION_PENALTY_CAP)
    score -= min(confirmed_fraud_count * CONFIRMED_FRAUD_PENALTY, CONFIRMED_FRAUD_PENALTY_CAP)
    if not has_recent_adverse_event and policy_count >= 2:
        score += RECOVERY_BONUS
    return round(_bounded(score, 0.0, 100.0), 2)


def recompute_trust_score(db: Session, worker: Worker, now: datetime | None = None) -> Worker:
    reference_time = now or utcnow()
    claims = list_claims_for_worker(db, worker.id)
    fraud_logs = list_fraud_logs_for_worker(db, worker.id)
    policies = list_policies_for_worker(db, worker.id)
    recent_threshold = reference_time - timedelta(days=30)

    approved_claim_count = sum(
        1 for claim in claims if claim.status in {ClaimStatus.auto_approved, ClaimStatus.paid}
    )
    manual_review_count = sum(1 for claim in claims if claim.status == ClaimStatus.manual_review)
    rejected_claim_count = sum(1 for claim in claims if claim.status == ClaimStatus.rejected)
    confirmed_fraud_count = sum(
        1
        for fraud_log in fraud_logs
        if float(fraud_log.fraud_score) >= 80.0 and fraud_log.action_taken == ClaimStatus.rejected
    )
    has_recent_adverse_event = any(
        claim.status in {ClaimStatus.manual_review, ClaimStatus.rejected}
        and ensure_utc(claim.created_at) >= recent_threshold
        for claim in claims
    ) or any(
        float(fraud_log.fraud_score) >= 40.0 and ensure_utc(fraud_log.created_at) >= recent_threshold
        for fraud_log in fraud_logs
    )

    worker.trust_score = compute_trust_score(
        kyc_verified=worker.kyc_verified,
        tenure_days=worker.tenure_days,
        policy_count=len(policies),
        approved_claim_count=approved_claim_count,
        manual_review_count=manual_review_count,
        rejected_claim_count=rejected_claim_count,
        confirmed_fraud_count=confirmed_fraud_count,
        has_recent_adverse_event=has_recent_adverse_event,
    )
    return update_worker(db, worker)
