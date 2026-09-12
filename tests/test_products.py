
import uuid

import pytest
import jwt

from config import settings

from app.models.user import User, UserRole
from app.models.product import Product


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

@pytest.fixture
def admin_token(db):
    """
    Create a temporary admin user and return a valid JWT.
    """

    email = f"product_admin_{uuid.uuid4().hex}@example.com"

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
# Create Product
# ---------------------------------------------------------

async def test_create_product_success(client, admin_token):
    response = await client.post(
        "/products/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Test Product",
            "price": 100.00,
            "stock_quantity": 10
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Product"
    assert data["price"] == 100.00
    assert data["stock_quantity"] == 10


async def test_create_product_negative_price(client, admin_token):
    response = await client.post(
        "/products/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Invalid Product",
            "price": -100,
            "stock_quantity": 10
        }
    )

    assert response.status_code == 422


async def test_create_product_zero_price(client, admin_token):
    response = await client.post(
        "/products/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Invalid Product",
            "price": 0,
            "stock_quantity": 10
        }
    )

    assert response.status_code == 422


async def test_create_product_negative_stock(client, admin_token):
    response = await client.post(
        "/products/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Invalid Product",
            "price": 100,
            "stock_quantity": -1
        }
    )

    assert response.status_code == 422


async def test_create_product_empty_name(client, admin_token):
    response = await client.post(
        "/products/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "",
            "price": 100,
            "stock_quantity": 10
        }
    )

    assert response.status_code == 422


async def test_create_product_missing_required_field(client, admin_token):
    response = await client.post(
        "/products/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Incomplete Product",
            "price": 100
        }
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# Authorization
# ---------------------------------------------------------

async def test_customer_cannot_create_product(client, auth_token):
    response = await client.post(
        "/products/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "name": "Customer Product",
            "price": 100,
            "stock_quantity": 10
        }
    )

    assert response.status_code == 403


async def test_customer_cannot_update_product(
    client,
    auth_token,
    test_product
):
    response = await client.patch(
        f"/products/{test_product.id}",
        headers={
            "Authorization": f"Bearer {auth_token}"
        },
        json={
            "price": 200
        }
    )

    assert response.status_code == 403


async def test_customer_cannot_delete_product(
    client,
    auth_token,
    test_product
):
    response = await client.delete(
        f"/products/{test_product.id}",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 403


async def test_product_create_without_token(client):
    response = await client.post(
        "/products/",
        json={
            "name": "Unauthorized Product",
            "price": 100,
            "stock_quantity": 10
        }
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# Get Product
# ---------------------------------------------------------

async def test_get_product_success(client, auth_token, test_product):
    response = await client.get(
        f"/products/{test_product.id}",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == test_product.id
    assert data["name"] == test_product.name


async def test_get_nonexistent_product(client, auth_token):
    response = await client.get(
        "/products/999999999",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# Product List
# ---------------------------------------------------------

async def test_get_products(client, auth_token):
    response = await client.get(
        "/products/",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_products_invalid_skip(client, auth_token):
    response = await client.get(
        "/products/?skip=-1",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 422


async def test_get_products_invalid_limit_zero(client, auth_token):
    response = await client.get(
        "/products/?limit=0",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 422


async def test_get_products_limit_above_maximum(client, auth_token):
    response = await client.get(
        "/products/?limit=101",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# Update Product
# ---------------------------------------------------------

async def test_update_product_success(
    client,
    admin_token,
    test_product
):
    response = await client.patch(
        f"/products/{test_product.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "price": 250
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["price"] == 250


async def test_update_product_empty_body(
    client,
    admin_token,
    test_product
):
    response = await client.patch(
        f"/products/{test_product.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={}
    )

    assert response.status_code == 400


async def test_update_nonexistent_product(client, admin_token):
    response = await client.patch(
        "/products/999999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "price": 200
        }
    )

    assert response.status_code == 404


async def test_update_product_negative_price(
    client,
    admin_token,
    test_product
):
    response = await client.patch(
        f"/products/{test_product.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "price": -50
        }
    )

    assert response.status_code == 422


async def test_update_product_negative_stock(
    client,
    admin_token,
    test_product
):
    response = await client.patch(
        f"/products/{test_product.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "stock_quantity": -10
        }
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# Delete Product
# ---------------------------------------------------------

async def test_delete_product_success(
    client,
    admin_token,
    db
):
    product = Product(
        name=f"Delete Test {uuid.uuid4().hex}",
        price=100,
        stock_quantity=10,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    product_id = product.id

    response = await client.delete(
        f"/products/{product_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Product Deleted Successfully"

    deleted_product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    assert deleted_product is None


async def test_delete_nonexistent_product(client, admin_token):
    response = await client.delete(
        "/products/999999999",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 404

