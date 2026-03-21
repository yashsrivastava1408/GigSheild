from __future__ import annotations

from pathlib import Path
import sys
from datetime import timedelta

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.time import utcnow
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.claim import Claim
from app.models.disruption_event import DisruptionEvent
from app.models.enums import ClaimStatus, PaymentMethod, PayoutProfileStatus
from app.models.fraud_log import FraudLog
from app.models.policy import Policy
from app.models.plausibility_assessment import PlausibilityAssessment
from app.models.payout import Payout
from app.models.worker import Worker
from app.schemas.disruption import DisruptionEventCreateRequest
from app.schemas.policy import PolicyPurchaseRequest
from app.schemas.worker import WorkerCreateRequest
from app.services.claims import create_automatic_claims
from app.services.admin import approve_claim
from app.services.disruptions import create_event
from app.services.policies import purchase_policy
from app.services.workers import register_worker


def _reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _delete_all(db) -> None:
    for model in (
        PlausibilityAssessment,
        FraudLog,
        Payout,
        Claim,
        DisruptionEvent,
        Policy,
        Worker,
    ):
        db.query(model).delete()
    db.commit()


def _seed_high_trust_worker(db, *, phone: str, name: str, platform: str, zone_id: str, earnings: int, tenure: int):
    return register_worker(
        db,
        WorkerCreateRequest(
            phone=phone,
            name=name,
            platform=platform,
            zone_id=zone_id,
            device_fingerprint=None,
            avg_weekly_earnings=earnings,
            tenure_days=tenure,
            kyc_verified=True,
        ),
    )


def _seed_low_trust_worker(db, *, phone: str, name: str, platform: str, zone_id: str, earnings: int, tenure: int):
    return register_worker(
        db,
        WorkerCreateRequest(
            phone=phone,
            name=name,
            platform=platform,
            zone_id=zone_id,
            device_fingerprint=None,
            avg_weekly_earnings=earnings,
            tenure_days=tenure,
            kyc_verified=False,
        ),
    )


def _mark_pending_upi_profile(db, worker, upi_id: str):
    worker.payout_method = PaymentMethod.upi
    worker.payout_upi_id = upi_id
    worker.payout_contact_name = worker.name
    worker.payout_contact_phone = worker.phone
    worker.payout_profile_status = PayoutProfileStatus.pending
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


def main() -> None:
    _reset_database()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _delete_all(db)

        chennai_worker = _seed_high_trust_worker(
            db,
            phone="9990011223",
            name="Ravi Kumar",
            platform="zomato",
            zone_id="chennai_zone_4",
            earnings=3800,
            tenure=210,
        )
        mumbai_worker = _seed_low_trust_worker(
            db,
            phone="9990011224",
            name="Asha Patil",
            platform="swiggy",
            zone_id="mumbai_zone_2",
            earnings=3200,
            tenure=12,
        )
        delhi_worker = _seed_high_trust_worker(
            db,
            phone="9990011225",
            name="Imran Sheikh",
            platform="blinkit",
            zone_id="delhi_zone_7",
            earnings=4400,
            tenure=340,
        )
        bengaluru_worker = _seed_high_trust_worker(
            db,
            phone="9990011226",
            name="Neha Reddy",
            platform="zepto",
            zone_id="bengaluru_zone_3",
            earnings=4100,
            tenure=150,
        )
        chennai_manual_worker = _seed_low_trust_worker(
            db,
            phone="9990011227",
            name="Farhan Ali",
            platform="swiggy",
            zone_id="chennai_zone_4",
            earnings=3000,
            tenure=8,
        )

        shared_device_fingerprint = "seed-demo-device-clone-001"
        chennai_worker.device_fingerprint = shared_device_fingerprint
        mumbai_worker.device_fingerprint = shared_device_fingerprint
        db.add(chennai_worker)
        db.add(mumbai_worker)
        db.commit()
        db.refresh(chennai_worker)
        db.refresh(mumbai_worker)

        _mark_pending_upi_profile(db, mumbai_worker, "asha-demo@upi")
        _mark_pending_upi_profile(db, bengaluru_worker, "neha-demo@upi")
        _mark_pending_upi_profile(db, chennai_manual_worker, "farhan-demo@upi")

        chennai_policy, _, _ = purchase_policy(
            db, PolicyPurchaseRequest(worker_id=chennai_worker.id, coverage_tier="standard")
        )
        mumbai_policy, _, _ = purchase_policy(db, PolicyPurchaseRequest(worker_id=mumbai_worker.id, coverage_tier="basic"))
        delhi_policy, _, _ = purchase_policy(db, PolicyPurchaseRequest(worker_id=delhi_worker.id, coverage_tier="premium"))
        bengaluru_policy, _, _ = purchase_policy(
            db, PolicyPurchaseRequest(worker_id=bengaluru_worker.id, coverage_tier="standard")
        )
        chennai_manual_policy, _, _ = purchase_policy(
            db, PolicyPurchaseRequest(worker_id=chennai_manual_worker.id, coverage_tier="basic")
        )

        chennai_event = create_event(
            db,
            DisruptionEventCreateRequest(
                event_type="heavy_rain",
                zone_id="chennai_zone_4",
                severity=3,
                started_at=utcnow() - timedelta(hours=1),
                verified=True,
                weather_api_raw={"source": "seed_demo", "label": "rainstorm", "rainfall_mm_per_hr": 19},
            ),
        )
        mumbai_event = create_event(
            db,
            DisruptionEventCreateRequest(
                event_type="curfew",
                zone_id="mumbai_zone_2",
                severity=2,
                started_at=utcnow() - timedelta(minutes=45),
                verified=True,
                weather_api_raw={"source": "seed_demo", "label": "curfew", "curfew": True},
            ),
        )
        delhi_event = create_event(
            db,
            DisruptionEventCreateRequest(
                event_type="aqi",
                zone_id="delhi_zone_7",
                severity=4,
                started_at=utcnow() - timedelta(minutes=20),
                verified=True,
                weather_api_raw={"source": "seed_demo", "label": "smog_spike", "aqi": 450},
            ),
        )
        bengaluru_event = create_event(
            db,
            DisruptionEventCreateRequest(
                event_type="extreme_heat",
                zone_id="bengaluru_zone_3",
                severity=2,
                started_at=utcnow() - timedelta(minutes=35),
                verified=True,
                weather_api_raw={"source": "seed_demo", "label": "heatwave", "temp_c": 44},
            ),
        )

        chennai_summary = create_automatic_claims(db, chennai_event.id)
        mumbai_summary = create_automatic_claims(db, mumbai_event.id)
        delhi_summary = create_automatic_claims(db, delhi_event.id)
        bengaluru_summary = create_automatic_claims(db, bengaluru_event.id)

        manual_review_claims = [claim for claim in db.query(Claim).all() if claim.status == ClaimStatus.manual_review]
        if manual_review_claims:
            approve_claim(db, manual_review_claims[0].id)

        print("Seed complete")
        print(
            f"Workers: {[worker.id for worker in (chennai_worker, mumbai_worker, delhi_worker, bengaluru_worker, chennai_manual_worker)]}"
        )
        print(
            f"Policies: {[chennai_policy.id, mumbai_policy.id, delhi_policy.id, bengaluru_policy.id, chennai_manual_policy.id]}"
        )
        print(f"Events: {[chennai_event.id, mumbai_event.id, delhi_event.id, bengaluru_event.id]}")
        print(
            "Auto-claim summaries:",
            {
                "chennai": chennai_summary.model_dump(),
                "mumbai": mumbai_summary.model_dump(),
                "delhi": delhi_summary.model_dump(),
                "bengaluru": bengaluru_summary.model_dump(),
            },
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
