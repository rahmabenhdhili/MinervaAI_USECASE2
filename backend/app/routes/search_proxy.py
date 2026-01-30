from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.events_service import track_event
from app.core.auth_utils import get_user_id_from_token

# teammate search imports (READ-ONLY)
from scripts.search_B2B import SemanticSearchAgent
from scripts.embedding_agent_B2B import EmbeddingAgent

router = APIRouter(prefix="/search", tags=["search"])

# initialize teammate components
embedding_agent = EmbeddingAgent()
search_agent = SemanticSearchAgent(embedding_agent)

# Request schema
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/")
async def search(req: SearchRequest, request: Request):
    """
    1️⃣ Extract user_id from JWT token
    2️⃣ Track search event automatically
    3️⃣ Call teammate search and return results
    """
    # Step 1: get user_id securely from JWT
    user_id = get_user_id_from_token(request)

    # Step 2: track the search in Mongo
    await track_event(user_id=user_id, event_type="search", content=req.query)

    # Step 3: delegate search to teammate code
    results = search_agent.search(req.query, top_k=req.top_k)

    return {"results": results}
