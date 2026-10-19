from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.order import OrderItemResponse, OrderItemCreate, OrderCreate, OrderResponse
from app.core.dependencies import get_current_user,require_admin
from app.models.user import User,UserRole
from app.models.product import Product
from app.models.order import Status,Order
from app.models.order_item import OrderItem
from app.events.events import Event, EventType
from app.events.publisher import publish_event
from decimal import Decimal




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

        total_amount = sum(
        (
            products[product_id].price * quantities[product_id]
            for product_id in quantities
        ),
        Decimal("0.00"),
        )

        new_order=Order(
            user_id=current_user.id,
            status=Status.PENDING,
            total_amount=total_amount
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
                quantity=quantity,
                unit_price=product.price
            )

            db.add(order_item)

        db.commit()

        event = Event(
            event_type=EventType.ORDER_CREATED,
            data={
                "order_id": new_order.id,
                "user_id": current_user.id,
                "status": new_order.status.value,
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": quantities[product_id]
                    }
                    for product_id in sorted(quantities)
                ]
            }
        )

        publish_event(event)

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


@router.delete("/{order_id}", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        order = (
            db.query(Order)
            .filter(Order.id == order_id)
            .first()
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )

        if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own orders"
            )

        if order.status == Status.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order is already cancelled"
            )

        if order.status != Status.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only confirmed orders can be cancelled"
            )

        order_items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order.id)
            .all()
        )

        product_ids = sorted(
            item.product_id for item in order_items
        )

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
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {product_id} not found"
                )

            products[product_id] = product

        for item in order_items:
            products[item.product_id].stock_quantity += item.quantity

        order.status = Status.CANCELLED

        db.commit()
        db.refresh(order)

        event = Event(
            event_type=EventType.ORDER_CANCELLED,
            data={
                "order_id": order.id,
                "user_id": order.user_id,
                "status": order.status.value,
                "items": [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity
                    }
                    for item in order_items
                ]
            }
        )

        publish_event(event)

        return order

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
                 
