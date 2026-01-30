from fastapi import APIRouter
from datetime import datetime
from app.database_sqlite import get_events_collection
from app.database import get_events_collection
from app.models.event import EventCreate

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/track")
async def track_event(event: EventCreate):
    """
    Tracks user actions (search or click) and stores them in SQLite.
    Tracks user actions (search or click) and stores them in MongoDB.
    
    Example for search:
    {
        "user_id": "42",
        "type": "search",
        "content": "cahier 200 pages"
    }

    Example for click:
    {
        "user_id": "42",
        "type": "click",
        "content": "Cahier 200 pages Staedtler Fournitures scolaires Meuble Plus Monastir"
    }
    """
    events_db = get_events_collection()  # get the events database

    # Insert the event
    event_id = events_db.track_event({
        "user_id": event.user_id,
        "event_type": event.type,
        "content": event.content
    })

    # Respond with success
    return {"status": "tracked", "event_id": event_id}
    events = get_events_collection()  # get the events collection

    # Insert the event with timestamp
    await events.insert_one({
        "user_id": event.user_id,
        "type": event.type,
        "content": event.content,
        "timestamp": datetime.utcnow()  # store UTC timestamp
    })

    # Respond with success
    return {"status": "tracked"}
