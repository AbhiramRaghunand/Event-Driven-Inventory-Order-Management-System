from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class OrderItem(Base):
    __tablename__="order_items"
    __table_args__ = (
            CheckConstraint("quantity > 0", name="ck_order_quantity_positive"),
        )

    id=Column(Integer,primary_key=True)
    order_id=Column(Integer,ForeignKey("orders.id",ondelete="CASCADE"),nullable=False)
    product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False)
    quantity=Column(Integer,nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
