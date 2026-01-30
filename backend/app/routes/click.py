from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.events_service import track_event
from app.core.auth_utils import get_user_id_from_token

router = APIRouter(prefix="/click", tags=["click"])

class ClickRequest(BaseModel):
    product_name: str
    brand: str | None = None
    category: str | None = None
    supplier: str | None = None

@router.post("/")
async def click(req: ClickRequest, request: Request):
    """
    1️⃣ Extract user_id from JWT token
    2️⃣ Merge product info into semantic content
    3️⃣ Track click event automatically
    """
    # Step 1: get user_id securely from JWT
    user_id = get_user_id_from_token(request)

    # Step 2: merge info into one string for semantic tracking
    content = " ".join(filter(None, [
        req.product_name,
        req.brand,
        req.category,
        req.supplier
    ]))

    # Step 3: track click
    await track_event(user_id=user_id, event_type="click", content=content)

    return {"status": "tracked"}
