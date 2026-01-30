from datetime import datetime
from app.database_sqlite import user_db

def get_events_collection():
    return user_db

async def track_event(user_id: str, event_type: str, content: str):
    """
    Store a user interaction (search or click) in SQLite.
    This is pure tracking — no AI here.
    """
    return user_db.track_event({
        "user_id": user_id,
        "event_type": event_type,
        "content": content
from app.database import db

def get_events_collection():
    return db["events"]

async def track_event(user_id: str, event_type: str, content: str):
    """
    Store a user interaction (search or click) in MongoDB.
    This is pure tracking — no AI here.
    """
    await get_events_collection().insert_one({
        "user_id": user_id,
        "type": event_type,   # "search" or "click"
        "content": content,
        "timestamp": datetime.utcnow()
    })
