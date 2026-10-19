
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentCreateResponse(BaseModel):
    payment_id: int
    order_id: int
    amount: Decimal
    currency: str
    status: str
    razorpay_order_id: str
    razorpay_key_id: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=1)
    razorpay_payment_id: str = Field(min_length=1)
    razorpay_signature: str = Field(min_length=1)


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    currency: str
    status: str
    provider: str
    provider_order_id: str | None = None
    provider_payment_id: str | None = None
