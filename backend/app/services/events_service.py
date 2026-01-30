from datetime import datetime
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
