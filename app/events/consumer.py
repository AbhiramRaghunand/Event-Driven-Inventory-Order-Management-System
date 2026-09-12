from app.events.events import Event, EventType
from app.events.publisher import event_queue
from app.core.database import SessionLocal
from app.models.events import EventLog
from app.models.product import Product
from app.events.publisher import publish_event
from app.models.notification import Notification
import threading
import time
import json

LOW_STOCK_THRESHOLD = 5

def consume_event() -> Event | None:
    if event_queue.empty():
        return None

    event = event_queue.get()

    db = SessionLocal()

    try:
        existing_event = (
            db.query(EventLog)
            .filter(EventLog.event_id == str(event.event_id))
            .first()
        )

        if existing_event is not None:
            print(f"Event already processed: {event.event_id}")
            return event

        event_log = EventLog(
            event_id=str(event.event_id),
            event_type=event.event_type.value,
            event_data=json.loads(json.dumps(event.data, default=str))
        )

        db.add(event_log)
        db.commit()

        if event.event_type == EventType.PRODUCT_CREATED:
            print(f"Processing PRODUCT_CREATED event: {event.data}")

        elif event.event_type == EventType.PRODUCT_UPDATED:
            print(f"Processing PRODUCT_UPDATED event: {event.data}")

        elif event.event_type == EventType.PRODUCT_DELETED:
            print(f"Processing PRODUCT_DELETED event: {event.data}")

        elif event.event_type == EventType.ORDER_CREATED:
            print(f"Processing ORDER_CREATED event: {event.data}")

            notification = Notification(
                user_id=event.data["user_id"],
                event_type=EventType.ORDER_CREATED.value,
                message=f"Your order #{event.data['order_id']} has been confirmed."
            )

            db.add(notification)
            db.commit()

            for item in event.data["items"]:
                product = (
                    db.query(Product)
                    .filter(Product.id == item["product_id"])
                    .first()
                )

                if product is None:
                    continue

                current_stock = product.stock_quantity
                previous_stock = current_stock + item["quantity"]

                if (
                    previous_stock > LOW_STOCK_THRESHOLD
                    and current_stock <= LOW_STOCK_THRESHOLD
                ):
                    low_stock_event = Event(
                        event_type=EventType.LOW_STOCK,
                        data={
                            "product_id": product.id,
                            "name": product.name,
                            "stock_quantity": current_stock,
                        },
                    )

                    publish_event(low_stock_event)

        elif event.event_type == EventType.ORDER_CANCELLED:
            print(f"Processing ORDER_CANCELLED event: {event.data}")
            notification = Notification(
                user_id=event.data["user_id"],
                event_type=EventType.ORDER_CANCELLED.value,
                message=f"Your order #{event.data['order_id']} has been cancelled."
            )

            db.add(notification)
            db.commit()

        elif event.event_type == EventType.LOW_STOCK:
            print(f"LOW STOCK ALERT: {event.data}")

        return event

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def start_event_consumer():
    def worker():
        while True:
            event = consume_event()

            if event is None:
                time.sleep(0.5)
                continue

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()