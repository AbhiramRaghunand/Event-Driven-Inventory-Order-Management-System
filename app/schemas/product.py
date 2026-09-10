from pydantic import BaseModel,Field

class ProductCreate(BaseModel):
    name: str=Field(min_length=1)
    price: float =Field(gt=0)
    stock_quantity: int=Field(ge=0)

class ProductUpdate(BaseModel):
    name: str|None=Field(default=None,min_length=1)
    price: float|None=Field(default=None,gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)

class ProductResponse(BaseModel):
    id:int
    name: str
    price: float
    stock_quantity: int

    model_config = {"from_attributes": True}
