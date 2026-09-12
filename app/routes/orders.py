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

@router.post("/",response_model=OrderResponse,status_code=status.HTTP_201_CREATED)
def create_order(order:OrderCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    try:
        if current_user.role != UserRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers can place orders"
            )

        quantities={}
        for item in order.items:
            quantities[item.product_id]=(
                quantities.get(item.product_id,0)+item.quantity
            )

        products={}
        for product_id in sorted(quantities):
            product=db.query(Product).filter(Product.id==product_id).with_for_update().first()

            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Product {product_id} not found")

            quantity=quantities[product_id]
            if product.stock_quantity<quantity:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Insufficient quantity for product {product.id}")

            products[product_id]=product

        new_order=Order(
            user_id=current_user.id,
            status=Status.CONFIRMED
        )

        db.add(new_order)
        db.flush()

        for product_id in sorted(quantities):
            product=products[product_id]
            quantity=quantities[product_id]

            product.stock_quantity-=quantity

            order_item=OrderItem(
                order_id=new_order.id,
                product_id=product_id,
                quantity=quantity
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

                 
