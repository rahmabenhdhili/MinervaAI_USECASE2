# Core Configuration
from app.database_sqlite import get_events_collection

async def get_user_preference_text(user_id: str, limit: int = 20) -> str:
    """
    Fetch the last 'limit' events for a user and merge them into one string.
    This string will represent the user's preference for personalization.
    """
    events_db = get_events_collection()
    return events_db.get_user_preference_text(user_id, limit)
