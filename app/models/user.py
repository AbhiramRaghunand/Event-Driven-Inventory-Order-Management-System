from enum import Enum as PyEnum
from sqlalchemy import Integer, String, Column, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(PyEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class User(Base):
    __tablename__="users"

    id=Column(Integer,primary_key=True,index=True)
    email=Column(String,unique=True,nullable=False)
    password_hash=Column(String,nullable=False)
    role=Column(Enum(UserRole), nullable=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

    orders = relationship("Order", back_populates="user")
