import hashlib
import hmac
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.enums import PolicyPaymentStatus
from app.models.webhook_event import WebhookEvent
from app.repositories.policy_payments import (
    get_policy_payment_by_order_id,
    get_policy_payment_by_payment_id,
    update_policy_payment,
)
from app.repositories.webhook_events import create_webhook_event, get_webhook_event


router = APIRouter()


@router.post("/razorpay/webhook")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
) -> dict[str, bool]:
    if not settings.razorpay_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook secret is not configured.")
    raw_body = await request.body()
    expected_signature = hmac.new(
        settings.razorpay_webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not x_razorpay_signature or not hmac.compare_digest(expected_signature, x_razorpay_signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature.")

    payload = await request.json()
    event_id = str(payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id") or payload.get("id") or uuid4())
    event_type = str(payload.get("event") or "unknown")

    db = SessionLocal()
    try:
        if get_webhook_event(db, event_id) is not None:
            return {"accepted": True, "duplicate": True}

        create_webhook_event(
            db,
            WebhookEvent(
                id=str(uuid4()),
                provider="razorpay",
                provider_event_id=event_id,
                event_type=event_type,
                payload=payload,
            ),
        )

        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
        order_id = str(payment_entity.get("order_id") or order_entity.get("id") or "")
        payment_id = str(payment_entity.get("id") or "")
        policy_payment = None
        if order_id:
            policy_payment = get_policy_payment_by_order_id(db, order_id)
        if policy_payment is None and payment_id:
            policy_payment = get_policy_payment_by_payment_id(db, payment_id)

        if policy_payment is not None:
            policy_payment.raw_payload = payload
            if event_type in {"payment.captured", "order.paid"}:
                policy_payment.status = PolicyPaymentStatus.paid
                policy_payment.razorpay_payment_id = payment_id or policy_payment.razorpay_payment_id
            elif event_type == "payment.failed":
                policy_payment.status = PolicyPaymentStatus.failed
            update_policy_payment(db, policy_payment)

        return {"accepted": True, "duplicate": False}
    finally:
        db.close()
