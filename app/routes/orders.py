from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.order import OrderItemResponse, OrderItemCreate, OrderCreate, OrderResponse
from app.core.dependencies import get_current_user,require_admin
from app.models.user import User,UserRole
from app.models.product import Product
from app.models.order import Status,Order
from app.models.order_item import OrderItem




router=APIRouter(prefix="/orders",tags=["Orders"])

@router.post("/",response_model=OrderResponse)
def create_order(order:OrderCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    try:
        if current_user.role != UserRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers can place orders"
            )
        products=[]
        for item in order.items:
            product=db.query(Product).filter(Product.id==item.product_id).first()

            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")

            if product.stock_quantity<item.quantity:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Insufficient quantity for product {product.id}")

            products.append(product)

        new_order=Order(
            user_id=current_user.id,
            status=Status.CONFIRMED
        )

        db.add(new_order)
        db.flush()

        for item,product in zip(order.items,products):
            product.stock_quantity-=item.quantity

            order_item=OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=item.quantity
            )

            db.add(order_item)

        db.commit()

        return new_order
    
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{order_id}",response_model=OrderResponse)
def get_order(order_id:int, db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    order=db.query(Order).filter(Order.id==order_id).first()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders",
        )

    return order


@router.get("/",response_model=list[OrderResponse])
def get_orders(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):

    if current_user.role==UserRole.ADMIN:
        orders=db.query(Order).all()
    else:
        orders=db.query(Order).filter(Order.user_id==current_user.id).all()


    return orders

                 
