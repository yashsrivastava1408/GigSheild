import base64
import hashlib
import hmac
import uuid
from decimal import Decimal

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models.enums import PaymentMethod, PolicyPaymentStatus, PayoutProfileStatus, PayoutStatus
from app.models.policy_payment import PolicyPayment
from app.models.payout import Payout
from app.repositories.policy_payments import create_policy_payment, get_policy_payment_by_order_id, update_policy_payment
from app.repositories.payouts import create_payout
from app.repositories.workers import update_worker
from app.schemas.policy import PolicyPurchaseRequest, PolicyPurchaseVerification
from app.schemas.premium import PremiumQuoteResponse


def is_live_payment_enabled() -> bool:
    return (
        not settings.use_mock_payouts
        and bool(settings.razorpay_key_id.strip())
        and bool(settings.razorpay_key_secret.strip())
    )


def is_live_claim_payout_enabled() -> bool:
    return is_live_payment_enabled() and bool(settings.razorpayx_source_account_number.strip())


def create_policy_checkout_order(
    payload: PolicyPurchaseRequest,
    quote: PremiumQuoteResponse,
) -> dict[str, str | int | bool]:
    amount_paise = int((Decimal(str(quote.weekly_premium)) * Decimal("100")).quantize(Decimal("1")))
    if not is_live_payment_enabled():
        return {
            "checkout_required": False,
            "key_id": "",
            "order_id": "",
            "amount": amount_paise,
            "currency": settings.razorpay_currency,
        }

    response = httpx.post(
        "https://api.razorpay.com/v1/orders",
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
        json={
            "amount": amount_paise,
            "currency": settings.razorpay_currency,
            "receipt": encode_checkout_notes(payload.worker_id, payload.coverage_tier.value)[:40],
            "notes": {
                "worker_id": payload.worker_id,
                "coverage_tier": payload.coverage_tier.value,
            },
        },
        timeout=10.0,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create a Razorpay order.",
        ) from exc

    order = response.json()
    return {
        "checkout_required": True,
        "key_id": settings.razorpay_key_id,
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": settings.razorpay_currency,
    }


def record_policy_checkout(db: Session, payload: PolicyPurchaseRequest, order: dict[str, str | int | bool], quote: PremiumQuoteResponse) -> PolicyPayment | None:
    order_id = str(order["order_id"])
    if not order_id:
        return None
    existing = get_policy_payment_by_order_id(db, order_id)
    if existing is not None:
        return existing
    return create_policy_payment(
        db,
        PolicyPayment(
            id=str(uuid.uuid4()),
            worker_id=payload.worker_id,
            coverage_tier=payload.coverage_tier,
            amount=float(quote.weekly_premium),
            currency=settings.razorpay_currency,
            razorpay_order_id=order_id,
            idempotency_key=f"policy-order-{order_id}",
            status=PolicyPaymentStatus.created,
            raw_payload={"checkout": order},
        ),
    )


def verify_policy_payment(db: Session, payment: PolicyPurchaseVerification | None) -> PolicyPayment | None:
    if not is_live_payment_enabled():
        return None

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay payment verification is required before activating a policy.",
        )

    message = f"{payment.razorpay_order_id}|{payment.razorpay_payment_id}".encode("utf-8")
    expected_signature = hmac.new(
        settings.razorpay_key_secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, payment.razorpay_signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Razorpay payment signature.")
    policy_payment = get_policy_payment_by_order_id(db, payment.razorpay_order_id)
    if policy_payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found.")
    if policy_payment.policy_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment order already used.")
    policy_payment.razorpay_payment_id = payment.razorpay_payment_id
    policy_payment.signature_verified = True
    policy_payment.status = PolicyPaymentStatus.verified
    policy_payment.raw_payload = {
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
    }
    return update_policy_payment(db, policy_payment)


def encode_checkout_notes(worker_id: str, coverage_tier: str) -> str:
    raw = f"{worker_id}:{coverage_tier}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def attach_payment_to_policy(db: Session, payment: PolicyPayment | None, policy_id: str) -> None:
    if payment is None:
        return
    payment.policy_id = policy_id
    update_policy_payment(db, payment)


def issue_claim_payout(db: Session, worker, claim, amount: float) -> Payout:
    idempotency_key = f"claim-payout-{claim.id}"
    if settings.use_mock_payouts:
        return create_payout(
            db,
            Payout(
                id=str(uuid.uuid4()),
                claim_id=claim.id,
                worker_id=claim.worker_id,
                amount=amount,
                payment_method=worker.payout_method or PaymentMethod.upi,
                razorpay_payment_id=f"mock_{claim.id[:8]}",
                idempotency_key=idempotency_key,
                failure_reason=None,
                status=PayoutStatus.completed,
            ),
        )

    if worker.payout_profile_status != PayoutProfileStatus.verified:
        return create_payout(
            db,
            Payout(
                id=str(uuid.uuid4()),
                claim_id=claim.id,
                worker_id=claim.worker_id,
                amount=amount,
                payment_method=worker.payout_method or PaymentMethod.upi,
                razorpay_payment_id=f"pending_{claim.id[:8]}",
                idempotency_key=idempotency_key,
                failure_reason="Payout profile is not verified.",
                status=PayoutStatus.pending,
            ),
        )

    if not is_live_claim_payout_enabled():
        reference = f"mock_{claim.id[:8]}"
        status_value = PayoutStatus.pending
        failure_reason = "RazorpayX source account is not configured."
        return create_payout(
            db,
            Payout(
                id=str(uuid.uuid4()),
                claim_id=claim.id,
                worker_id=claim.worker_id,
                amount=amount,
                payment_method=worker.payout_method or PaymentMethod.upi,
                razorpay_payment_id=reference,
                idempotency_key=idempotency_key,
                failure_reason=failure_reason,
                status=status_value,
            ),
        )

    try:
        contact_payload = {
            "name": worker.payout_contact_name or worker.name,
            "contact": worker.payout_contact_phone or worker.phone,
            "type": "employee",
            "reference_id": worker.id,
        }
        contact_response = httpx.post(
            "https://api.razorpay.com/v1/contacts",
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            json=contact_payload,
            timeout=10.0,
        )
        contact_response.raise_for_status()
        contact_id = contact_response.json()["id"]

        if worker.payout_method == PaymentMethod.bank_transfer:
            fund_account_request = {
                "contact_id": contact_id,
                "account_type": "bank_account",
                "bank_account": {
                    "name": worker.payout_bank_account_name,
                    "ifsc": worker.payout_bank_ifsc,
                    "account_number": worker.payout_bank_account_number,
                },
            }
        else:
            fund_account_request = {
                "contact_id": contact_id,
                "account_type": "vpa",
                "vpa": {"address": worker.payout_upi_id},
            }

        fund_account_id = worker.payout_fund_account_id
        if not fund_account_id:
            fund_response = httpx.post(
                "https://api.razorpay.com/v1/fund_accounts",
                auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
                json=fund_account_request,
                timeout=10.0,
            )
            fund_response.raise_for_status()
            fund_account_id = fund_response.json()["id"]
            worker.payout_fund_account_id = fund_account_id
            update_worker(db, worker)

        payout_response = httpx.post(
            "https://api.razorpay.com/v1/payouts",
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            headers={"X-Payout-Idempotency": idempotency_key},
            json={
                "account_number": settings.razorpayx_source_account_number,
                "fund_account_id": fund_account_id,
                "amount": int((Decimal(str(amount)) * Decimal("100")).quantize(Decimal("1"))),
                "currency": settings.razorpay_currency,
                "mode": "UPI" if worker.payout_method == PaymentMethod.upi else "IMPS",
                "purpose": "payout",
                "reference_id": claim.id,
                "narration": "GigShield claim payout",
            },
            timeout=10.0,
        )
        payout_response.raise_for_status()
    except httpx.HTTPError as exc:
        return create_payout(
            db,
            Payout(
                id=str(uuid.uuid4()),
                claim_id=claim.id,
                worker_id=claim.worker_id,
                amount=amount,
                payment_method=worker.payout_method or PaymentMethod.upi,
                razorpay_payment_id=f"failed_{claim.id[:8]}",
                idempotency_key=idempotency_key,
                failure_reason=str(exc),
                status=PayoutStatus.failed,
            ),
        )

    payout_payload = payout_response.json()
    provider_status = str(payout_payload.get("status") or "").lower()
    if provider_status in {"processed"}:
        status_value = PayoutStatus.completed
    elif provider_status in {"queued", "pending", "processing"}:
        status_value = PayoutStatus.processing
    else:
        status_value = PayoutStatus.failed

    return create_payout(
        db,
        Payout(
            id=str(uuid.uuid4()),
            claim_id=claim.id,
            worker_id=claim.worker_id,
            amount=amount,
            payment_method=worker.payout_method or PaymentMethod.upi,
            razorpay_payment_id=str(payout_payload.get("id") or f"payout_{claim.id[:8]}"),
            idempotency_key=idempotency_key,
            failure_reason=None if status_value != PayoutStatus.failed else str(payout_payload),
            status=status_value,
            processed_at=utcnow(),
        ),
    )
