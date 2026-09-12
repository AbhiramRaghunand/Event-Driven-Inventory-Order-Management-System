
import uuid

import pytest
import jwt

from config import settings

from app.models.user import User, UserRole
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------
# Admin fixture
# ---------------------------------------------------------

@pytest.fixture
def admin_token(db):
    """
    Create a temporary admin user and return a valid JWT.
    """

    email = f"order_admin_{uuid.uuid4().hex}@example.com"

    admin = User(
        email=email,
        password_hash="test_password_hash",
        role=UserRole.ADMIN,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    payload = {
        "sub": str(admin.id),
        "role": admin.role.value,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    yield token

    db.delete(admin)
    db.commit()


# ---------------------------------------------------------
# Create Order - Success
# ---------------------------------------------------------

async def test_create_order_success(
    client,
    auth_token,
    test_product,
    db
):
    initial_stock = test_product.stock_quantity

    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"]
    assert data["status"] == "confirmed"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == test_product.id
    assert data["items"][0]["quantity"] == 1

    db.refresh(test_product)

    assert test_product.stock_quantity == initial_stock - 1


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

async def test_create_order_without_token(client, test_product):
    response = await client.post(
        "/orders/",
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 401


async def test_create_order_with_malformed_token(
    client,
    test_product
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": "Bearer invalid-token"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# Authorization
# ---------------------------------------------------------

async def test_admin_cannot_create_order(
    client,
    admin_token,
    test_product
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 403


# ---------------------------------------------------------
# Order Input Validation
# ---------------------------------------------------------

async def test_create_order_quantity_zero(
    client,
    auth_token,
    test_product
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 0
                }
            ]
        }
    )

    assert response.status_code == 422


async def test_create_order_negative_quantity(
    client,
    auth_token,
    test_product
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": -5
                }
            ]
        }
    )

    assert response.status_code == 422


async def test_create_order_empty_items(
    client,
    auth_token
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": []
        }
    )

    assert response.status_code == 422


async def test_create_order_missing_items(
    client,
    auth_token
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={}
    )

    assert response.status_code == 422


async def test_create_order_invalid_product_id_type(
    client,
    auth_token
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": "abc",
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# Product Existence
# ---------------------------------------------------------

async def test_create_order_nonexistent_product(
    client,
    auth_token
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": 999999999,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# Stock Validation
# ---------------------------------------------------------

async def test_create_order_insufficient_stock(
    client,
    auth_token,
    test_product
):
    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": test_product.stock_quantity + 1
                }
            ]
        }
    )

    assert response.status_code == 409


async def test_create_order_exact_stock(
    client,
    auth_token,
    db
):
    product = Product(
        name=f"Exact Stock Product {uuid.uuid4().hex}",
        price=100,
        stock_quantity=5,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 5
                }
            ]
        }
    )

    assert response.status_code == 201

    db.refresh(product)

    assert product.stock_quantity == 0

    # Cleanup
    order_id = response.json()["id"]

    db.query(OrderItem).filter(
        OrderItem.order_id == order_id
    ).delete(synchronize_session=False)

    db.query(Order).filter(
        Order.id == order_id
    ).delete(synchronize_session=False)

    db.delete(product)
    db.commit()


# ---------------------------------------------------------
# Duplicate Product Items
# ---------------------------------------------------------

async def test_create_order_duplicate_product_items(
    client,
    auth_token,
    db
):
    product = Product(
        name=f"Duplicate Product {uuid.uuid4().hex}",
        price=100,
        stock_quantity=10,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 2
                },
                {
                    "product_id": product.id,
                    "quantity": 3
                }
            ]
        }
    )

    assert response.status_code == 201

    data = response.json()

    # Your implementation combines duplicate product IDs.
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product.id
    assert data["items"][0]["quantity"] == 5

    db.refresh(product)

    assert product.stock_quantity == 5

    # Cleanup
    order_id = data["id"]

    db.query(OrderItem).filter(
        OrderItem.order_id == order_id
    ).delete(synchronize_session=False)

    db.query(Order).filter(
        Order.id == order_id
    ).delete(synchronize_session=False)

    db.delete(product)
    db.commit()


# ---------------------------------------------------------
# Get Order
# ---------------------------------------------------------

async def test_get_own_order(
    client,
    auth_token,
    test_product
):
    create_response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    response = await client.get(
        f"/orders/{order_id}",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id


async def test_get_nonexistent_order(
    client,
    auth_token
):
    response = await client.get(
        "/orders/999999999",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 404


async def test_get_order_without_token(client):
    response = await client.get("/orders/1")

    assert response.status_code == 401


# ---------------------------------------------------------
# Order Ownership
# ---------------------------------------------------------

async def test_customer_cannot_view_another_users_order(
    client,
    db,
    test_product
):
    # Create first customer
    user1 = User(
        email=f"order_user1_{uuid.uuid4().hex}@example.com",
        password_hash="test_password_hash",
        role=UserRole.CUSTOMER,
    )

    # Create second customer
    user2 = User(
        email=f"order_user2_{uuid.uuid4().hex}@example.com",
        password_hash="test_password_hash",
        role=UserRole.CUSTOMER,
    )

    db.add_all([user1, user2])
    db.commit()

    db.refresh(user1)
    db.refresh(user2)

    token1 = jwt.encode(
        {
            "sub": str(user1.id),
            "role": user1.role.value,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    token2 = jwt.encode(
        {
            "sub": str(user2.id),
            "role": user2.role.value,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    # User 1 creates an order
    create_response = await client.post(
        "/orders/",
        headers={
            "Authorization": f"Bearer {token1}"
        },
        json={
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    # User 2 tries to access User 1's order
    response = await client.get(
        f"/orders/{order_id}",
        headers={
            "Authorization": f"Bearer {token2}"
        }
    )

    assert response.status_code == 403

    # Cleanup order
    db.query(OrderItem).filter(
        OrderItem.order_id == order_id
    ).delete(synchronize_session=False)

    db.query(Order).filter(
        Order.id == order_id
    ).delete(synchronize_session=False)

    db.delete(user1)
    db.delete(user2)
    db.commit()


# ---------------------------------------------------------
# Get Orders
# ---------------------------------------------------------

async def test_get_orders(
    client,
    auth_token
):
    response = await client.get(
        "/orders/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_orders_without_token(client):
    response = await client.get("/orders/")

    assert response.status_code == 401

