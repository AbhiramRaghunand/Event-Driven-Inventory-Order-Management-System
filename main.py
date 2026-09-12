from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.product import router as prod_router
from app.routes.orders import router as order_router



app = FastAPI(title="BEA API")
app.include_router(auth_router)
app.include_router(prod_router)
app.include_router(order_router)



@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
