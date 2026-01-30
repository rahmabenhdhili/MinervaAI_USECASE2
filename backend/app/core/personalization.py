from app.database_sqlite import get_events_collection

async def get_user_preference_text(user_id: str, limit: int = 10) -> str:
    """
    Build a semantic profile from the user's last interactions.
    """
    events_db = get_events_collection()
    return events_db.get_user_preference_text(user_id, limit)
