from fastapi import APIRouter
from app.core.personalization import get_user_preference_text
from app.core.qdrant_personalization import query_personalized_products

router = APIRouter(prefix="/home", tags=["home"])

@router.get("/{user_id}")
async def home(user_id: str):
    preference_text = await get_user_preference_text(user_id)

    if not preference_text:
        return {
            "recommended_products": [],
            "reason": "No history yet"
        }

    products = query_personalized_products(preference_text)

    return {
        "recommended_products": products,
        "reason": "Based on your last searches and clicks"
    }
