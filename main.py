from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.events.consumer import start_event_consumer

from app.routes.auth import router as auth_router
from app.routes.product import router as prod_router
from app.routes.orders import router as order_router
from app.routes.users import router as user_router
from app.routes.events import router as event_router
from app.routes.notifications import router as noti_router



app = FastAPI(title="BEA API")
start_event_consumer()
app.include_router(auth_router)
app.include_router(prod_router)
app.include_router(order_router)
app.include_router(user_router)
app.include_router(event_router)
app.include_router(noti_router)

app.mount(
    "/frontend",
    StaticFiles(
        directory="frontend",
        html=True
    ),
    name="frontend"
)


@app.exception_handler(Exception)
async def global_exception_handler( request: Request, exc: Exception ):
    return JSONResponse( 
        status_code=500, 
        content={ "detail": "Internal server error" } )


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
