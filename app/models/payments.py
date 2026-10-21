from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Numeric, Enum, DateTime, ForeignKey,
    CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PaymentStatus(PyEnum):
    CREATED = "created"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class RefundStatus(PyEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        UniqueConstraint("provider_order_id", name="uq_payment_provider_order_id"),
        UniqueConstraint("provider_payment_id", name="uq_payment_provider_payment_id"),
        UniqueConstraint("provider_refund_id", name="uq_payment_provider_refund_id"),
        UniqueConstraint("refund_idempotency_key", name="uq_payment_refund_idempotency_key"),
        CheckConstraint(
            "refund_amount IS NULL OR refund_amount > 0",
            name="ck_payment_refund_amount_positive",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.CREATED)
    provider = Column(String(30), nullable=False, default="razorpay")
    provider_order_id = Column(String(100), nullable=True)
    provider_payment_id = Column(String(100), nullable=True)

    provider_refund_id = Column(String(100), nullable=True)
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refund_status = Column(
        String(20), nullable=False, default=RefundStatus.NOT_REQUIRED.value,
        server_default=RefundStatus.NOT_REQUIRED.value,
    )
    refund_idempotency_key = Column(String(100), nullable=True)
    refund_error = Column(String(500), nullable=True)
    refund_created_at = Column(DateTime(timezone=True), nullable=True)
    refund_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order = relationship("Order", back_populates="payments")
