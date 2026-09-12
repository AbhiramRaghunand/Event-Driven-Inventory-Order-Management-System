from queue import Queue

from app.events.events import Event


event_queue = Queue()


def publish_event(event: Event) -> None:
    event_queue.put(event)