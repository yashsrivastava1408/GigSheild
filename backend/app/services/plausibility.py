from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import ensure_utc
from app.core.time import utcnow
from app.models.claim import Claim
from app.models.disruption_event import DisruptionEvent
from app.models.enums import ClaimStatus, RiskTier, RoutingDecision, SignalImpact
from app.models.plausibility_assessment import PlausibilityAssessment
from app.models.policy import Policy
from app.models.worker import Worker
from app.repositories.policies import list_active_policies_for_zone
from app.repositories.claims import (
    count_claims_for_event_since,
    get_claim_by_event_and_worker,
    list_claims_for_worker,
)
from app.repositories.fraud_logs import list_fraud_logs_for_worker
from app.repositories.plausibility_assessments import create_plausibility_assessment
from app.repositories.worker_zone_observations import list_recent_worker_zone_observations
from app.repositories.workers import list_workers_by_device_fingerprint
from app.schemas.plausibility import PlausibilitySignal


@dataclass(frozen=True)
class PlausibilityEvaluation:
    plausibility_score: int
    risk_tier: RiskTier
    routing_decision: RoutingDecision
    signals: list[PlausibilitySignal]


def _bounded(value: int, lower: int = 0, upper: int = 100) -> int:
    return max(lower, min(upper, value))


def _signal(code: str, description: str, impact: SignalImpact, weight: int, evidence: str) -> PlausibilitySignal:
    return PlausibilitySignal(
        code=code,
        description=description,
        impact=impact,
        weight=weight,
        evidence=evidence,
    )


def _risk_tier(score: int) -> RiskTier:
    if score >= 70:
        return RiskTier.low
    if score >= 40:
        return RiskTier.medium
    return RiskTier.high


def _routing_decision(score: int) -> RoutingDecision:
    if score >= 70:
        return RoutingDecision.approve
    if score >= 40:
        return RoutingDecision.manual_review
    return RoutingDecision.reject


def evaluate_claim_plausibility(
    db: Session,
    *,
    worker: Worker,
    policy: Policy,
    disruption_event: DisruptionEvent,
    claim_amount: float,
    trust_score: float,
    assessed_at: datetime | None = None,
) -> PlausibilityEvaluation:
    reference_time = assessed_at or utcnow()
    score = 50
    signals: list[PlausibilitySignal] = []
    recent_zone_observations = list_recent_worker_zone_observations(db, worker.id, reference_time - timedelta(days=30))
    active_policy_count = len(list_active_policies_for_zone(db, disruption_event.zone_id))

    duplicate_claim = get_claim_by_event_and_worker(db, worker.id, disruption_event.id)
    if duplicate_claim is not None:
        score -= 40
        signals.append(
            _signal(
                "DUPLICATE_CLAIM",
                "A claim for this worker and disruption already exists.",
                SignalImpact.negative,
                -40,
                f"existing_claim_id={duplicate_claim.id}",
            )
        )

    if trust_score < 40:
        score -= 25
        signals.append(
            _signal(
                "LOW_TRUST",
                "Worker trust score is below the low-risk threshold.",
                SignalImpact.negative,
                -25,
                f"trust_score={trust_score:.2f}",
            )
        )
    elif trust_score > 75:
        score += 20
        signals.append(
            _signal(
                "HIGH_TRUST",
                "Worker trust score is above the preferred threshold.",
                SignalImpact.positive,
                20,
                f"trust_score={trust_score:.2f}",
            )
        )

    policy_age = reference_time - ensure_utc(policy.created_at)
    if policy_age < timedelta(hours=24):
        score -= 18
        signals.append(
            _signal(
                "POLICY_TOO_NEW",
                "Policy was purchased too close to the claim event.",
                SignalImpact.negative,
                -18,
                f"policy_age_hours={policy_age.total_seconds() / 3600:.1f}",
            )
        )

    if worker.tenure_days < 30:
        score -= 10
        signals.append(
            _signal(
                "EARLY_LIFECYCLE",
                "Worker is still in the early lifecycle window, which increases claim scrutiny.",
                SignalImpact.negative,
                -10,
                f"tenure_days={worker.tenure_days}",
            )
        )

    if any(observation.zone_id == disruption_event.zone_id for observation in recent_zone_observations):
        score += 10
        signals.append(
            _signal(
                "ZONE_HISTORY_MATCH",
                "Worker has recent zone history that matches the disruption zone.",
                SignalImpact.positive,
                10,
                f"recent_zone_observations={len(recent_zone_observations)};zone_id={disruption_event.zone_id}",
            )
        )
    else:
        score -= 30
        signals.append(
            _signal(
                "ZONE_MISMATCH",
                "Worker has no recent zone history for this disruption zone.",
                SignalImpact.negative,
                -30,
                f"recent_zone_observations={len(recent_zone_observations)};zone_id={disruption_event.zone_id}",
            )
        )

    if worker.device_fingerprint:
        matching_workers = list_workers_by_device_fingerprint(db, worker.device_fingerprint)
        if len(matching_workers) > 1:
            score -= 35
            signals.append(
                _signal(
                    "DEVICE_CLONE",
                    "The same device fingerprint is linked to multiple worker accounts.",
                    SignalImpact.negative,
                    -35,
                    f"matching_workers={len(matching_workers)}",
                )
            )

    claim_ratio = claim_amount / float(policy.coverage_amount)
    if claim_amount <= float(policy.coverage_amount):
        score += 8
        signals.append(
            _signal(
                "AMOUNT_OK",
                "Claim amount stays within the purchased coverage.",
                SignalImpact.positive,
                8,
                f"claim_ratio={claim_ratio:.2f}",
            )
        )
    else:
        score -= 25
        signals.append(
            _signal(
                "SEVERITY_MISMATCH",
                "Claim amount exceeds the available coverage.",
                SignalImpact.negative,
                -25,
                f"claim_amount={claim_amount:.2f};coverage={float(policy.coverage_amount):.2f}",
            )
        )

    if disruption_event.verified:
        score += 12
        signals.append(
            _signal(
                "VERIFIED_TRIGGER",
                "External disruption was verified by a trigger feed.",
                SignalImpact.positive,
                12,
                f"event_type={disruption_event.event_type.value};zone_id={disruption_event.zone_id}",
            )
        )
    else:
        score -= 12
        signals.append(
            _signal(
                "UNVERIFIED_TRIGGER",
                "External disruption has not been verified yet.",
                SignalImpact.negative,
                -12,
                f"event_type={disruption_event.event_type.value};zone_id={disruption_event.zone_id}",
            )
        )

    weather_payload = disruption_event.weather_api_raw or {}
    weather_key = str(disruption_event.event_type.value)
    weather_ok = True
    if weather_key == "heavy_rain":
        rainfall = float(weather_payload.get("rainfall_mm_per_hr") or weather_payload.get("rainfall_mm") or 0)
        weather_ok = rainfall >= 15
    elif weather_key == "aqi":
        aqi = float(weather_payload.get("aqi") or 0)
        weather_ok = aqi >= 400
    elif weather_key == "flood":
        flood_level = int(weather_payload.get("flood_level") or 0)
        weather_ok = flood_level >= 2
    elif weather_key == "extreme_heat":
        temp = float(weather_payload.get("temp_c") or weather_payload.get("temperature_c") or 0)
        weather_ok = temp >= 43
    elif weather_key == "curfew":
        weather_ok = bool(weather_payload.get("curfew") or weather_payload.get("shutdown") or disruption_event.verified)
    elif weather_key == "outage":
        weather_ok = bool(weather_payload.get("outage_minutes") or disruption_event.verified)

    if weather_ok:
        score += 8
        signals.append(
            _signal(
                "WEATHER_MATCH",
                "Raw trigger data is consistent with the claimed disruption.",
                SignalImpact.positive,
                8,
                f"event_type={weather_key};payload_keys={','.join(sorted(weather_payload.keys()))}",
            )
        )
    else:
        score -= 25
        signals.append(
            _signal(
                "WEATHER_MISMATCH",
                "Raw trigger data does not match the claimed disruption.",
                SignalImpact.negative,
                -25,
                f"event_type={weather_key};payload_keys={','.join(sorted(weather_payload.keys()))}",
            )
        )

    co_claim_window_start = reference_time - timedelta(minutes=30)
    co_claim_count = count_claims_for_event_since(db, disruption_event.id, co_claim_window_start)
    if co_claim_count >= 3:
        score -= 20
        signals.append(
            _signal(
                "HIGH_CO_CLAIM_VELOCITY",
                "Too many claims are arriving on the same event in a short window.",
                SignalImpact.negative,
                -20,
                f"claims_in_30m={co_claim_count}",
            )
        )
    elif active_policy_count > 0 and co_claim_count <= max(1, active_policy_count // 5):
        score -= 10
        signals.append(
            _signal(
                "LOW_PEER_DENSITY",
                "Claim density is too low relative to the number of active workers in the zone.",
                SignalImpact.negative,
                -10,
                f"claims_in_30m={co_claim_count};active_policies={active_policy_count}",
            )
        )
    elif co_claim_count >= 2:
        score += 8
        signals.append(
            _signal(
                "PEER_CLUSTER",
                "Nearby workers are also filing claims on the same disruption.",
                SignalImpact.positive,
                8,
                f"claims_in_30m={co_claim_count};active_policies={active_policy_count}",
            )
        )

    rejected_claims = [
        existing_claim
        for existing_claim in list_claims_for_worker(db, worker.id)
        if existing_claim.status == ClaimStatus.rejected
    ]
    if rejected_claims:
        penalty = min(len(rejected_claims) * 18, 36)
        score -= penalty
        signals.append(
            _signal(
                "REJECTION_HISTORY",
                "Worker has prior rejected claims.",
                SignalImpact.negative,
                -penalty,
                f"rejected_claims={len(rejected_claims)}",
            )
        )

    fraud_logs = list_fraud_logs_for_worker(db, worker.id)
    if fraud_logs:
        score -= 30
        signals.append(
            _signal(
                "FRAUD_LOG_HIT",
                "Worker has prior fraud log activity.",
                SignalImpact.negative,
                -30,
                f"fraud_log_entries={len(fraud_logs)}",
            )
        )

    score = _bounded(score)
    risk_tier = _risk_tier(score)
    routing_decision = _routing_decision(score)
    return PlausibilityEvaluation(
        plausibility_score=score,
        risk_tier=risk_tier,
        routing_decision=routing_decision,
        signals=signals,
    )


def create_plausibility_record(
    db: Session,
    *,
    claim_id: str,
    evaluation: PlausibilityEvaluation,
) -> PlausibilityAssessment:
    return create_plausibility_assessment(
        db,
        PlausibilityAssessment(
            id=str(uuid.uuid4()),
            claim_id=claim_id,
            plausibility_score=evaluation.plausibility_score,
            risk_tier=evaluation.risk_tier,
            signals=[signal.model_dump() for signal in evaluation.signals],
            routing_decision=evaluation.routing_decision,
        ),
    )
