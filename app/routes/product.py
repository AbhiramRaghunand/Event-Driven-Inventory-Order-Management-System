from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductCreate,ProductUpdate,ProductResponse
from app.crud import product as crud_product
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

from app.events.events import Event, EventType
from app.events.publisher import publish_event

router=APIRouter(prefix="/products",tags=["Products"])

@router.post("/",response_model=ProductResponse)
def create_product(product:ProductCreate,db:Session=Depends(get_db),current_user:User=Depends(require_admin)):
    new_product = crud_product.create_product(db, product)

    event = Event(
        event_type=EventType.PRODUCT_CREATED,
        data={
            "product_id": new_product.id,
            "name": new_product.name,
            "price": new_product.price,
            "stock_quantity": new_product.stock_quantity
        }
    )

    publish_event(event)

    return new_product

@router.get("/", response_model=list[ProductResponse])
def get_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    return crud_product.get_products(db,skip,limit)

@router.get("/{product_id}",response_model=ProductResponse)
def get_product(product_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    product=crud_product.get_product(db,product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@router.patch("/{product_id}",response_model=ProductResponse)
def update_product(product_id:int,product:ProductUpdate,db:Session=Depends(get_db),current_user:User=Depends(require_admin)):
    if not product.model_dump(exclude_unset=True, exclude_none=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one product field is required",
        )

    db_product=crud_product.get_product(db,product_id)

    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
        )

    updated_product = crud_product.update_product(db, db_product, product)

    event = Event(
        event_type=EventType.PRODUCT_UPDATED,
        data={
            "product_id": updated_product.id,
            "name": updated_product.name,
            "price": updated_product.price,
            "stock_quantity": updated_product.stock_quantity
        }
    )

    publish_event(event)

    return updated_product

@router.delete("/{product_id}")
def delete_product(product_id:int, db:Session=Depends(get_db),current_user:User=Depends(require_admin)):
    db_prod=crud_product.get_product(db,product_id)

    if db_prod is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
            )

    crud_product.delete_product(db, db_prod)

    event = Event(
        event_type=EventType.PRODUCT_DELETED,
        data={
            "product_id": db_prod.id,
            "name": db_prod.name
        }
    )

    publish_event(event)

    return {
        "message": "Product Deleted Successfully"
    }


