from sqlalchemy.orm import Session

from app.repositories.disruptions import get_matching_active_event
from app.schemas.disruption import DisruptionEventCreateRequest
from app.services.disruptions import create_event
from app.services.providers import fetch_weather_signals


def sync_weather_events(db: Session) -> list:
    created_events = []
    for signal in fetch_weather_signals():
        if get_matching_active_event(db, signal.zone_id, signal.event_type) is not None:
            continue
        created_events.append(
            create_event(
                db,
                DisruptionEventCreateRequest(
                    event_type=signal.event_type,
                    zone_id=signal.zone_id,
                    severity=signal.severity,
                    started_at=signal.started_at,
                    ended_at=None,
                    weather_api_raw=signal.weather_api_raw,
                    verified=True,
                ),
            )
        )
    return created_events
