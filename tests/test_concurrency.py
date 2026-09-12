import asyncio

import pytest
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product


NUM_REQUESTS = 20


@pytest.mark.asyncio
async def test_concurrent_orders_for_single_stock_item(
    client,
    auth_token,
    test_user,
    test_product,
    db: Session,
):
    """
    Verify that only one concurrent order can purchase the final
    available unit of a product.
    """

    product_id = test_product.id

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }

    order_payload = {
        "items": [
            {
                "product_id": product_id,
                "quantity": 1,
            }
        ]
    }

    async def place_order():
        response = await client.post(
            "/orders/",
            json=order_payload,
            headers=headers,
        )

        return response

    # ---------------------------------------------------------
    # Send 20 requests concurrently.
    # ---------------------------------------------------------

    tasks = [
        place_order()
        for _ in range(NUM_REQUESTS)
    ]

    responses = await asyncio.gather(*tasks)

    # ---------------------------------------------------------
    # 1. Exactly one request must succeed.
    # ---------------------------------------------------------

    successful_responses = [
        response
        for response in responses
        if response.status_code == 201
    ]

    assert len(successful_responses) == 1, (
        f"Expected exactly 1 successful order, "
        f"but got {len(successful_responses)}"
    )

    # ---------------------------------------------------------
    # 2. The other 19 requests must return 409 Conflict.
    # ---------------------------------------------------------

    conflict_responses = [
        response
        for response in responses
        if response.status_code == 409
    ]

    assert len(conflict_responses) == NUM_REQUESTS - 1, (
        f"Expected {NUM_REQUESTS - 1} conflict responses, "
        f"but got {len(conflict_responses)}"
    )

    # ---------------------------------------------------------
    # 3. No unexpected HTTP status codes.
    # ---------------------------------------------------------

    unexpected_statuses = [
        response.status_code
        for response in responses
        if response.status_code not in {201, 409}
    ]

    assert unexpected_statuses == [], (
        f"Unexpected response status codes: {unexpected_statuses}"
    )

    # ---------------------------------------------------------
    # 4. Verify final stock is exactly 0.
    # ---------------------------------------------------------

    db.expire_all()

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    assert product is not None

    assert product.stock_quantity == 0, (
        f"Expected final stock to be 0, "
        f"but got {product.stock_quantity}"
    )

    # ---------------------------------------------------------
    # 5. Verify stock was never negative.
    # ---------------------------------------------------------

    assert product.stock_quantity >= 0

    # ---------------------------------------------------------
    # 6. Verify exactly one order was created.
    # ---------------------------------------------------------

    order_count = db.query(Order).filter(
        Order.user_id == test_user.id
    ).count()

    assert order_count == 1, (
        f"Expected exactly 1 order in the database, "
        f"but found {order_count}"
    )

    print("\n========== CONCURRENCY TEST RESULTS ==========")
    print(f"Total concurrent requests : {NUM_REQUESTS}")
    print(f"Successful orders         : {len(successful_responses)}")
    print(f"409 Conflict responses    : {len(conflict_responses)}")
    print(f"Final stock quantity      : {product.stock_quantity}")
    print(f"Orders created            : {order_count}")
    print("==============================================")