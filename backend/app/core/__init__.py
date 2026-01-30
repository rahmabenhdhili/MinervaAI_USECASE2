# Core Configuration
from app.database_sqlite import get_events_collection
from app.database import get_events_collection

async def get_user_preference_text(user_id: str, limit: int = 20) -> str:
    """
    Fetch the last 'limit' events for a user and merge them into one string.
    This string will represent the user's preference for personalization.
    """
    events_db = get_events_collection()
    return events_db.get_user_preference_text(user_id, limit)
    events = await get_events_collection().find(
        {"user_id": user_id}             # fetch events for this user
    ).sort("timestamp", -1).limit(limit).to_list(length=limit)  # newest first

    # Merge all 'content' into a single string
    merged_text = " ".join([e["content"] for e in events])
    return merged_text
