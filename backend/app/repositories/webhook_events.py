from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.webhook_event import WebhookEvent


def get_webhook_event(db: Session, provider_event_id: str) -> WebhookEvent | None:
    return db.scalar(select(WebhookEvent).where(WebhookEvent.provider_event_id == provider_event_id))


def create_webhook_event(db: Session, event: WebhookEvent) -> WebhookEvent:
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
