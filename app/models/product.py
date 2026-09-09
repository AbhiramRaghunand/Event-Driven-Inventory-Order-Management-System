from sqlalchemy import CheckConstraint, Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__="products"
    __table_args__ = (
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_quantity_nonnegative"),
        CheckConstraint("price>0", name="ck_product_price_positive")
    )

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,nullable=False)
    price=Column(Numeric(10,2),nullable=False)
    stock_quantity=Column(Integer,nullable=False,default=0)

    order_items = relationship("OrderItem", back_populates="product")
