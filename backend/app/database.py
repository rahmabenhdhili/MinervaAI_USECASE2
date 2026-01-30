from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client["personalization_db"]

def get_users_collection():
    return db["users"]
def get_events_collection():
    """
    Returns the MongoDB collection used to store user events
    """
    return db["events"] 
