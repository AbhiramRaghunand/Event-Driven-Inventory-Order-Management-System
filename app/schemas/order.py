from pydantic import BaseModel,Field
from app.models.order import Status
from datetime import datetime

class OrderItemCreate(BaseModel):
    product_id:int
    quantity:int=Field(default=1,gt=0)

class OrderCreate(BaseModel):
    items:list[OrderItemCreate]=Field(min_length=1)


class OrderItemResponse(BaseModel):
    id:int
    product_id: int
    quantity: int

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: Status
    created_at: datetime
    items: list[OrderItemResponse]