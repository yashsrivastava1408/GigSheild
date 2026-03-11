from datetime import UTC, datetime, timedelta

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.schemas.disruption import DisruptionEventCreateRequest
from app.schemas.policy import PolicyPurchaseRequest
from app.schemas.worker import WorkerCreateRequest
from app.services.claims import create_automatic_claims
from app.services.disruptions import create_event
from app.services.policies import purchase_policy
from app.services.workers import register_worker


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        worker = register_worker(
            db,
            WorkerCreateRequest(
                phone="9990011223",
                name="Ravi Kumar",
                platform="zomato",
                zone_id="chennai_zone_4",
                avg_weekly_earnings=3800,
                tenure_days=210,
                kyc_verified=True,
            ),
        )
        purchase_policy(db, PolicyPurchaseRequest(worker_id=worker.id, coverage_tier="standard"))
        event = create_event(
            db,
            DisruptionEventCreateRequest(
                event_type="heavy_rain",
                zone_id="chennai_zone_4",
                severity=3,
                started_at=datetime.now(UTC) - timedelta(hours=1),
                verified=True,
                weather_api_raw={"source": "seed_demo"},
            ),
        )
        summary = create_automatic_claims(db, event.id)
        print(f"Seeded demo worker {worker.id} and auto-claim summary: {summary.model_dump()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
