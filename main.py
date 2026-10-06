from fastapi import FastAPI,Request
from fastapi.responses import FileResponse, JSONResponse
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


@app.get("/")
def index() -> FileResponse:
    return FileResponse("frontend/index.html")


@app.get("/login")
def login_page() -> FileResponse:
    return FileResponse("frontend/pages/login/login.html")


@app.get("/register")
def register_page() -> FileResponse:
    return FileResponse("frontend/pages/register/register.html")


@app.get("/dashboard")
def dashboard_page() -> FileResponse:
    return FileResponse("frontend/pages/dashboard/dashboard.html")


@app.get("/products")
def products_page() -> FileResponse:
    return FileResponse("frontend/pages/products/products.html")


@app.get("/orders")
def orders_page() -> FileResponse:
    return FileResponse("frontend/pages/orders/orders.html")


@app.get("/cart")
def cart_page() -> FileResponse:
    return FileResponse("frontend/pages/cart/cart.html")


@app.get("/notifications")
def notifications_page() -> FileResponse:
    return FileResponse("frontend/pages/notifications/notifications.html")


@app.get("/events")
def events_page() -> FileResponse:
    return FileResponse("frontend/pages/events/events.html")


@app.get("/users")
def users_page() -> FileResponse:
    return FileResponse("frontend/pages/users/users.html")


@app.get("/profile")
def profile_page() -> FileResponse:
    return FileResponse("frontend/pages/profile/profile.html")


app.mount(
    "/assets",
    StaticFiles(directory="frontend/assets"),
    name="assets"
)

app.mount(
    "/page-assets",
    StaticFiles(directory="frontend/pages"),
    name="page-assets"
)


@app.exception_handler(Exception)
async def global_exception_handler( request: Request, exc: Exception ):
    return JSONResponse( 
        status_code=500, 
        content={ "detail": "Internal server error" } )


