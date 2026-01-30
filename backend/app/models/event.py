from pydantic import BaseModel

class EventCreate(BaseModel):
    user_id: str        # The ID of the user performing the action
    type: str           # "search" or "click" (type of event)
    content: str        # Text describing the event (search query or clicked product)
