"""Razorpay refund processing with persisted idempotency and retry support."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import requests
from sqlalchemy.orm import Session

from config import settings
from app.events.events import Event, EventType
from app.events.publisher import publish_event
from app.models.order import Order
from app.models.payments import Payment, PaymentStatus

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


def utc_now():
    return datetime.now(timezone.utc)


def _publish_refund_status(payment: Payment, order: Order, status_value: str) -> None:
    publish_event(Event(
        event_type=EventType.REFUND_STATUS_UPDATED,
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "payment_id": payment.id,
            "refund_id": payment.provider_refund_id,
            "refund_status": status_value,
            "refund_amount": str(payment.refund_amount or payment.amount),
        },
    ))


def prepare_refund(payment: Payment) -> None:
    """Persist a stable request before calling Razorpay, so crashes are retryable."""
    if payment.refund_status == "processed":
        return
    if payment.refund_status != "pending":
        payment.refund_status = "pending"
        payment.refund_amount = Decimal(str(payment.amount)).quantize(Decimal("0.01"))
        payment.refund_idempotency_key = uuid4().hex
        payment.refund_created_at = utc_now()
        payment.refund_error = None
    elif not payment.refund_idempotency_key:
        payment.refund_idempotency_key = uuid4().hex
        payment.refund_amount = Decimal(str(payment.amount)).quantize(Decimal("0.01"))
        payment.refund_created_at = payment.refund_created_at or utc_now()
    payment.refund_updated_at = utc_now()


def _apply_provider_response(db: Session, payment: Payment, order: Order, body: dict) -> dict:
    old_status = payment.refund_status
    refund_id = body.get("id")
    if refund_id:
        payment.provider_refund_id = refund_id

    provider_status = str(body.get("status", "pending")).lower()
    if provider_status not in {"pending", "processed", "failed"}:
        provider_status = "pending"

    payment.refund_status = provider_status
    payment.refund_error = None if provider_status != "failed" else "Razorpay reported that the refund failed."
    payment.refund_updated_at = utc_now()
    if provider_status == "processed":
        payment.status = PaymentStatus.REFUNDED
    # Keep original payment status SUCCESS while a refund is pending/failed.
    db.commit()
    db.refresh(payment)

    if old_status != provider_status:
        _publish_refund_status(payment, order, provider_status)

    return {
        "order_id": order.id,
        "payment_id": payment.id,
        "refund_id": payment.provider_refund_id,
        "refund_amount": str(payment.refund_amount or payment.amount),
        "refund_status": payment.refund_status,
    }


def process_refund(db: Session, payment: Payment, order: Order, *, allow_retry: bool = False) -> dict:
    """Create a full refund or reconcile a known refund without duplicate requests."""
    if payment.status not in (PaymentStatus.SUCCESS, PaymentStatus.REFUNDED):
        raise ValueError("Only a successfully paid order can be refunded.")
    if not payment.provider_payment_id:
        payment.refund_status = "failed"
        payment.refund_error = "The verified Razorpay payment ID is missing."
        payment.refund_updated_at = utc_now()
        db.commit()
        return {
            "order_id": order.id, "payment_id": payment.id,
            "refund_id": None, "refund_amount": str(payment.amount),
            "refund_status": "failed",
        }
    if payment.refund_status == "processed" or payment.status == PaymentStatus.REFUNDED:
        return {
            "order_id": order.id, "payment_id": payment.id,
            "refund_id": payment.provider_refund_id,
            "refund_amount": str(payment.refund_amount or payment.amount),
            "refund_status": "processed",
        }

    # A provider-confirmed failed refund can be retried with a new key. For an
    # uncertain network result, keep the old key and exact same request body.
    if payment.refund_status == "failed" and allow_retry:
        payment.refund_status = "pending"
        payment.refund_idempotency_key = uuid4().hex
        payment.provider_refund_id = None
        payment.refund_error = None
        payment.refund_amount = Decimal(str(payment.amount)).quantize(Decimal("0.01"))
        payment.refund_created_at = utc_now()
        payment.refund_updated_at = utc_now()
        db.commit()
    elif payment.refund_status != "pending":
        prepare_refund(payment)
        db.commit()
    elif not payment.refund_idempotency_key:
        prepare_refund(payment)
        db.commit()

    # If Razorpay gave us a refund ID, ask Razorpay for its latest state rather
    # than issuing a second refund request.
    if payment.provider_refund_id:
        try:
            from app.core.razorpay_client import razorpay_client
            response = razorpay_client.payment.fetch_refund_id(
                payment.provider_payment_id, payment.provider_refund_id
            )
            return _apply_provider_response(db, payment, order, dict(response))
        except Exception as exc:
            payment.refund_error = f"Could not refresh refund status: {str(exc)[:400]}"
            payment.refund_updated_at = utc_now()
            db.commit()
            return {
                "order_id": order.id, "payment_id": payment.id,
                "refund_id": payment.provider_refund_id,
                "refund_amount": str(payment.refund_amount or payment.amount),
                "refund_status": "pending",
            }

    amount_paise = int(Decimal(str(payment.refund_amount or payment.amount)) * 100)
    url = f"{RAZORPAY_API_BASE}/payments/{payment.provider_payment_id}/refund"
    headers = {"X-Refund-Idempotency": payment.refund_idempotency_key}
    payload = {
        "amount": amount_paise,
        "receipt": f"refund_order_{order.id}_payment_{payment.id}",
        "notes": {"internal_order_id": str(order.id), "payment_record_id": str(payment.id)},
    }

    try:
        response = requests.post(
            url,
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            headers=headers,
            json=payload,
            timeout=20,
        )
        if response.status_code == 409:
            # Same idempotency key is already being processed. Retry later with
            # the same key and payload; do not create a new refund request.
            payment.refund_status = "pending"
            payment.refund_error = "Razorpay is still processing this refund request."
            payment.refund_updated_at = utc_now()
            db.commit()
            return {
                "order_id": order.id, "payment_id": payment.id,
                "refund_id": payment.provider_refund_id,
                "refund_amount": str(payment.refund_amount or payment.amount),
                "refund_status": "pending",
            }

        if response.status_code >= 400:
            body_text = response.text[:400]
            # 5xx responses can be ambiguous; retain pending state and the same
            # key. Definitive 4xx responses are recorded as failed for safe retry.
            if response.status_code >= 500:
                payment.refund_status = "pending"
            else:
                payment.refund_status = "failed"
            payment.refund_error = body_text
            payment.refund_updated_at = utc_now()
            db.commit()
            if payment.refund_status == "failed":
                _publish_refund_status(payment, order, "failed")
            return {
                "order_id": order.id, "payment_id": payment.id,
                "refund_id": payment.provider_refund_id,
                "refund_amount": str(payment.refund_amount or payment.amount),
                "refund_status": payment.refund_status,
            }

        return _apply_provider_response(db, payment, order, response.json())

    except requests.RequestException as exc:
        # A timeout can happen after Razorpay created the refund. Keep the key
        # and pending status; a retry with the same key is safe.
        payment.refund_status = "pending"
        payment.refund_error = f"Refund outcome is not yet confirmed: {str(exc)[:400]}"
        payment.refund_updated_at = utc_now()
        db.commit()
        return {
            "order_id": order.id, "payment_id": payment.id,
            "refund_id": payment.provider_refund_id,
            "refund_amount": str(payment.refund_amount or payment.amount),
            "refund_status": "pending",
        }
