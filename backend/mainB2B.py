from fastapi import FastAPI
from app.routes import auth, home, search_proxy, click
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from scripts.embedding_agent_B2B import EmbeddingAgent
from scripts.qroq_explainerB2B import GroqExplainer
from scripts.search_B2B import SemanticSearchAgent
from scripts.price_optimizeB2B import PriceOptimizer
import os
from datetime import datetime
from fastapi import Depends
from app.database import get_events_collection
from app.core.security import get_current_user_id  # JWT helper



app = FastAPI()

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Instantiate agents
agent = EmbeddingAgent()
search_agent = SemanticSearchAgent(agent)
price_optimizer = PriceOptimizer()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
explainer = GroqExplainer(api_key=GROQ_API_KEY)

# Request schema search
class SearchRequest(BaseModel):
    product_name: str
    quantity: int = 1
    max_price: float = None

# Request schema click
class ClickRequest(BaseModel):
    product_name: str
    brand: str
    category: str
    supplier: str    

@app.post("/search")
async def search_best_supplier_endpoint(
    req: SearchRequest,
    user_id: str = Depends(get_current_user_id)  # <-- automatically extract user from JWT
):
    # --- 1️⃣ Log search in Mongo automatically ---
    events = get_events_collection()
    await events.insert_one({
        "user_id": user_id,
        "type": "search",
        "content": req.product_name,
        "timestamp": datetime.utcnow()
    })

    # --- 2️⃣ Call teammate's search agent ---
    products = search_agent.search(req.product_name, top_k=20)

    # --- 3️⃣ Optimize products ---
    optimized_products = price_optimizer.optimize(
        products=products,
        quantity=req.quantity,
        max_price=req.max_price,
        query=req.product_name
    )

    # --- 4️⃣ Return results ---
    if not optimized_products:
        return {
            "best_product": None,
            "alternatives": [],
            "explanation": "No products match your criteria."
        }

    best_supplier = optimized_products[0]
    alternatives = [
        p for p in optimized_products[1:]
        if p["total_price"] > best_supplier["total_price"]
        and (req.max_price is None or p["total_price"] <= req.max_price)
    ][:3]

    explanation = explainer.explain_choice(
        best_supplier=best_supplier,
        query=req.product_name,
        quantity=req.quantity
    )

    return {
        "best_product": best_supplier,
        "alternatives": alternatives,
        "explanation": explanation
    }

@app.post("/click")
async def click_endpoint(
    req: ClickRequest,
    user_id: str = Depends(get_current_user_id)
):
    events = get_events_collection()
    await events.insert_one({
        "user_id": user_id,
        "type": "click",
        "content": req.product_name,
        "timestamp": datetime.utcnow()
    })
    return {"status": "ok", "message": "Click recorded automatically"}



# Include auth and personalization routes
app.include_router(auth.router)
app.include_router(search_proxy.router)
app.include_router(click.router)
app.include_router(home.router)