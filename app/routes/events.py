from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.events import EventLog


router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


@router.get("/")
def get_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    events = (
        db.query(EventLog)
        .order_by(EventLog.processed_at.desc())
        .all()
    )

    return [
        {
            "id": event.id,
            "event_id": event.event_id,
            "event_type": event.event_type,
            "event_data": event.event_data,
            "processed_at": event.processed_at
        }
        for event in events
    ]


@router.get("/{event_id}")
def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    event = (
        db.query(EventLog)
        .filter(EventLog.event_id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return {
        "id": event.id,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "event_data": event.event_data,
        "processed_at": event.processed_at
    }