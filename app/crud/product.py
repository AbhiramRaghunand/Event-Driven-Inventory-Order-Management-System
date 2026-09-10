from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate,ProductUpdate


def create_product(db:Session,product:ProductCreate):
    new_product=Product(
        name=product.name,
        price=product.price,
        stock_quantity=product.stock_quantity
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product

def get_product(db:Session,product_id:int):
    return db.query(Product).filter(Product.id==product_id).first()

def get_products(db:Session,skip:int=0,limit:int=0):
    return db.query(Product).offset(skip).limit(limit).all()

def update_product(db: Session, db_product: Product, product: ProductUpdate):
    update_data = product.model_dump(exclude_unset=True, exclude_none=True)

    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)

    return db_product

def delete_product(db:Session,product:Product):
    db.delete(product)
    db.commit()
