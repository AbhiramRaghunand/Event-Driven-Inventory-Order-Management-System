from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductCreate,ProductUpdate,ProductResponse
from app.crud import product as crud_product
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router=APIRouter(prefix="/products",tags=["Products"])

@router.post("/",response_model=ProductResponse)
def create_product(product:ProductCreate,db:Session=Depends(get_db),current_user:User=Depends(require_admin)):
    return crud_product.create_product(db,product)

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

    return crud_product.update_product(db,db_product,product)

@router.delete("/{product_id}")
def delete_product(product_id:int, db:Session=Depends(get_db),current_user:User=Depends(require_admin)):
    db_prod=crud_product.get_product(db,product_id)

    if db_prod is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
            )

    crud_product.delete_product(db,db_prod)

    return {
        "message":"Product Deleted Successfully"
    }


