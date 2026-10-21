
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from razorpay.errors import SignatureVerificationError

from app.schemas.payments import PaymentVerifyRequest

from app.core.database import get_db
from app.core.razorpay_client import razorpay_client, RAZORPAY_KEY_ID
from app.models.order import Order, Status
from app.models.payments import Payment, PaymentStatus
from app.models.user import User, UserRole
from app.schemas.payments import PaymentCreateResponse
from app.core.dependencies import get_current_user
from app.events.events import Event, EventType
from app.events.publisher import publish_event
from app.models.order_item import OrderItem
from app.models.product import Product
from app.services.refunds import process_refund

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/orders/{order_id}",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can initiate payments",
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != Status.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be paid",
        )

    existing_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .order_by(Payment.id.desc())
        .first()
    )

    if existing_payment is not None:
        if existing_payment.status == PaymentStatus.SUCCESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This order has already been paid",
            )

        if existing_payment.status in (
            PaymentStatus.CREATED,
            PaymentStatus.PENDING,
        ):
            # Reuse the existing Razorpay order for another attempt.
            return PaymentCreateResponse(
                payment_id=existing_payment.id,
                order_id=order.id,
                amount=existing_payment.amount,
                currency=existing_payment.currency,
                status=existing_payment.status.value,
                razorpay_order_id=existing_payment.provider_order_id,
                razorpay_key_id=RAZORPAY_KEY_ID,
            )

    amount = Decimal(str(order.total_amount)).quantize(Decimal("0.01"))

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order amount must be greater than zero",
        )

    amount_in_paise = int(amount * 100)

    try:
        razorpay_order = razorpay_client.order.create(
            data={
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"order_{order.id}",
                "notes": {
                    "internal_order_id": str(order.id),
                    "customer_id": str(current_user.id),
                },
            }
        )

        payment = Payment(
            order_id=order.id,
            amount=amount,
            currency="INR",
            status=PaymentStatus.CREATED,
            provider="razorpay",
            provider_order_id=razorpay_order["id"],
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return PaymentCreateResponse(
            payment_id=payment.id,
            order_id=order.id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status.value,
            razorpay_order_id=razorpay_order["id"],
            razorpay_key_id=RAZORPAY_KEY_ID,
        )

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create payment. Please try again.",
        ) from exc



@router.post("/verify")
def verify_payment(
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can verify payments",
        )

    payment = (
        db.query(Payment)
        .join(Order, Payment.order_id == Order.id)
        .filter(
            Order.user_id == current_user.id,
            Payment.provider_order_id == payload.razorpay_order_id,
        )
        .with_for_update()
        .first()
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found",
        )

    if payment.status == PaymentStatus.SUCCESS:
        if payment.provider_payment_id == payload.razorpay_payment_id:
            return {
                "message": "Payment already verified",
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "status": payment.status.value,
            }

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment has already been completed",
        )

    if payment.status not in (
        PaymentStatus.CREATED,
        PaymentStatus.PENDING,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This payment cannot be verified",
        )

    try:
        razorpay_client.utility.verify_payment_signature(
            {
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
            }
        )
    except SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment verification could not be completed",
        )

    order = (
        db.query(Order)
        .filter(Order.id == payment.order_id)
        .with_for_update()
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated order not found",
        )

    if order.status == Status.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This order has been cancelled",
        )

    payment.status = PaymentStatus.SUCCESS
    payment.provider_payment_id = payload.razorpay_payment_id
    order.status = Status.CONFIRMED

    try:
        db.commit()
        db.refresh(payment)
        db.refresh(order)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the verified payment",
        )

    event = Event(
        event_type=EventType.ORDER_CONFIRMED,
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "status": order.status.value,
            "payment_id": payment.id,
            "amount": str(payment.amount),
        },
    )
    publish_event(event)

    try:
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the verified payment",
        )

    return {
        "message": "Payment verified successfully",
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "status": payment.status.value,
    }



@router.post("/orders/{order_id}/cancel")
def cancel_unpaid_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can cancel their pending orders",
        )

    try:
        order = (
            db.query(Order)
            .filter(
                Order.id == order_id,
                Order.user_id == current_user.id,
            )
            .with_for_update()
            .first()
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if order.status == Status.CANCELLED:
            return {
                "message": "Order is already cancelled",
                "order_id": order.id,
                "status": order.status.value,
            }

        if order.status != Status.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending orders can be cancelled this way",
            )

        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order.id)
            .with_for_update()
            .first()
        )

        if payment is not None:
            if payment.status == PaymentStatus.SUCCESS:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Payment already succeeded; order cannot be cancelled",
                )

            if payment.provider_order_id:
                razorpay_order = razorpay_client.order.fetch(
                    payment.provider_order_id
                )

                if razorpay_order.get("status") == "paid":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Payment may have succeeded. Reconcile payment before cancelling.",
                    )

        order_items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order.id)
            .all()
        )

        product_ids = sorted({item.product_id for item in order_items})
        products = {}

        for product_id in product_ids:
            product = (
                db.query(Product)
                .filter(Product.id == product_id)
                .with_for_update()
                .first()
            )

            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product {product_id} is missing; stock was not restored",
                )

            products[product_id] = product

        for item in order_items:
            products[item.product_id].stock_quantity += item.quantity

        order.status = Status.CANCELLED

        if payment is not None and payment.status in (
            PaymentStatus.CREATED,
            PaymentStatus.PENDING,
        ):
            payment.status = PaymentStatus.FAILED

        db.commit()
        db.refresh(order)

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not safely cancel the pending order",
        ) from exc

    event = Event(
        event_type=EventType.ORDER_CANCELLED,
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "status": order.status.value,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                }
                for item in order_items
            ],
        },
    )
    publish_event(event)

    return {
        "message": "Pending order cancelled and stock restored",
        "order_id": order.id,
        "status": order.status.value,
    }



@router.get("/orders/{order_id}/refund")
def get_refund_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own refund status")
    payment = db.query(Payment).filter(Payment.order_id == order.id).order_by(Payment.id.desc()).first()
    if payment is None:
        return {"order_id": order.id, "refund_status": "not_required", "refund_id": None, "refund_amount": None}
    return {
        "order_id": order.id,
        "payment_id": payment.id,
        "payment_status": payment.status.value,
        "refund_id": payment.provider_refund_id,
        "refund_amount": str(payment.refund_amount) if payment.refund_amount is not None else None,
        "refund_status": payment.refund_status,
        "refund_error": payment.refund_error,
        "refund_created_at": payment.refund_created_at,
        "refund_updated_at": payment.refund_updated_at,
    }


@router.post("/orders/{order_id}/refund/retry")
def retry_order_refund(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .with_for_update()
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only retry refunds for your own orders")
    if order.status != Status.CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only cancelled orders can be refunded")

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .order_by(Payment.id.desc())
        .with_for_update()
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No payment record exists for this order")
    if payment.status not in (PaymentStatus.SUCCESS, PaymentStatus.REFUNDED):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This order does not have a successfully paid payment to refund")

    try:
        result = process_refund(db, payment, order, allow_retry=True)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reconcile refund status. Please retry shortly.") from exc
    return {"message": "Refund status checked", **result}
