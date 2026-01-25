from fastapi import APIRouter, HTTPException
from app.mcp.qdrant_tools import (
    search_products_by_vector,
    filter_products_by_budget,
    get_collection_stats,
    calculate_budget_metrics
)
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/mcp", tags=["mcp-tools"])

class SearchRequest(BaseModel):
    query_text: str
    collection_name: str = "products_pc"
    max_price: Optional[float] = None
    category: Optional[str] = None
    limit: int = 10
    use_mmr: bool = True

class FilterRequest(BaseModel):
    products_json: str
    budget: float
    include_over_budget: bool = True
    over_budget_percentage: float = 0.2

class MetricsRequest(BaseModel):
    products_json: str
    budget: float

@router.post("/search")
async def mcp_search_products(request: SearchRequest):
    """
    FastMCP tool endpoint: Search products by vector similarity
    """
    try:
        result = search_products_by_vector(
            query_text=request.query_text,
            collection_name=request.collection_name,
            max_price=request.max_price,
            category=request.category,
            limit=request.limit,
            use_mmr=request.use_mmr
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/filter")
async def mcp_filter_products(request: FilterRequest):
    """
    FastMCP tool endpoint: Filter products by budget
    """
    try:
        result = filter_products_by_budget(
            products_json=request.products_json,
            budget=request.budget,
            include_over_budget=request.include_over_budget,
            over_budget_percentage=request.over_budget_percentage
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{collection_name}")
async def mcp_collection_stats(collection_name: str):
    """
    FastMCP tool endpoint: Get collection statistics
    """
    try:
        result = get_collection_stats(collection_name)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics")
async def mcp_budget_metrics(request: MetricsRequest):
    """
    FastMCP tool endpoint: Calculate budget metrics
    """
    try:
        result = calculate_budget_metrics(
            products_json=request.products_json,
            budget=request.budget
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
