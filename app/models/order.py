from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from sqlalchemy.sql import func
from app.core.database import Base

class Status(PyEnum):
    PENDING="pending"
    CONFIRMED="confirmed"
    CANCELLED="cancelled"

class Order(Base):
    __tablename__="orders"

    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False)
    status=Column(Enum(Status),default=Status.PENDING,nullable=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    total_amount=Column(Numeric(10,2),nullable=False,default=0)
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem",back_populates="order",cascade="all, delete-orphan",passive_deletes=True,)
    payments = relationship(
    "Payment",
    back_populates="order",
    cascade="all, delete-orphan",
)