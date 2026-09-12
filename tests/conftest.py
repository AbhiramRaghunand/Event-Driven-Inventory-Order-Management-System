import uuid

import pytest
import pytest_asyncio
import httpx
import jwt

from sqlalchemy.orm import Session

from main import app
from config import settings

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem


@pytest.fixture
def db():
    """
    Provide a database session for test setup and cleanup.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db: Session):
    """
    Create a temporary customer for the concurrency test.
    """

    email = f"concurrency_test_{uuid.uuid4().hex}@example.com"

    user = User(
        email=email,
        password_hash="test_password_hash",
        role=UserRole.CUSTOMER,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    # Remove orders belonging to this test user first.
    orders = db.query(Order).filter(
        Order.user_id == user.id
    ).all()

    for order in orders:
        db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).delete(synchronize_session=False)

    for order in orders:
        db.delete(order)

    db.delete(user)
    db.commit()


@pytest.fixture
def test_product(db: Session):
    """
    Create a product with exactly 1 item in stock.
    """

    product = Product(
        name=f"Concurrency Test Product {uuid.uuid4().hex}",
        price=100,
        stock_quantity=1,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    yield product

    # Delete any order items referencing this product.
    db.query(OrderItem).filter(
        OrderItem.product_id == product.id
    ).delete(synchronize_session=False)

    db.delete(product)
    db.commit()


@pytest.fixture
def auth_token(test_user):
    """
    Create a JWT accepted by the application's get_current_user().
    """

    payload = {
        "sub": str(test_user.id)
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


@pytest_asyncio.fixture
async def client():
    """
    Create an async HTTP client connected directly to the FastAPI app.
    """

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        yield client