import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8000/orders/"

TOKEN_A = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzg5MjI4Mzg2fQ.2tLzRBt6kiVXTUbAXZM5_RXQys3AJn8a-AFs_4vtzVQ"
TOKEN_B = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwicm9sZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzg5MjI4NDIwfQ.h5PH1ygjZOPe8DlFGks-ScwC0IVU3Kfu7x0i2qTzKso"

ORDER_DATA = {
    "items": [
        {
            "product_id": 4,
            "quantity": 2
        }
    ]
}


def place_order(token):
    response = requests.post(
        URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=ORDER_DATA
    )

    return response.status_code, response.json()


with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [
        executor.submit(place_order, TOKEN_A),
        executor.submit(place_order, TOKEN_B)
    ]

    for future in futures:
        status_code, response = future.result()
        print(status_code, response)