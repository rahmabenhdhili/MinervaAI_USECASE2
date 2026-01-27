from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from scripts.embedding_agent_B2B import EmbeddingAgent
from scripts.qroq_explainerB2B import GroqExplainer
from scripts.search_B2B import SemanticSearchAgent
from scripts.price_optimizeB2B import PriceOptimizer
import os

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

# Request schema
class SearchRequest(BaseModel):
    product_name: str
    quantity: int = 1
    max_price: float = None

@app.post("/search")
def search_best_supplier_endpoint(req: SearchRequest):
    # Semantic search
    products = search_agent.search(req.product_name, top_k=20)

    # Optimize and filter products by quantity and max_price
    optimized_products = price_optimizer.optimize(
        products=products,
        quantity=req.quantity,
        max_price=req.max_price,
        query=req.product_name
    )

    if not optimized_products:
        return {
            "best_product": None,
            "alternatives": [],
            "explanation": "No products match your criteria."
        }

    # Best supplier = first product after optimization
    best_supplier = optimized_products[0]

    # Alternatives = next 3 products more expensive than best_supplier but within max_price
    alternatives = [
        p for p in optimized_products[1:]
        if p["total_price"] > best_supplier["total_price"]
        and (req.max_price is None or p["total_price"] <= req.max_price)
    ][:3]

    # Generate explanation using GroqExplainer
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
