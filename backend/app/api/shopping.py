from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.models.schemas import (
    ShoppingSearchRequest, ShoppingSearchResponse, 
    AddToCartRequest, CartResponse,
    RecommendedProduct, Product, Explanation, VirtualCart
)
from app.services.hybrid_embedding_service import hybrid_embedding_service
from app.services.prototype_service import prototype_service
from app.services.qdrant_service import qdrant_service
from app.services.groq_service import groq_service
from app.services.cart_service import cart_service
from app.services.cache_service import cache_service
from app.services.price_comparison_service import price_comparison_service
from app.services.hybrid_search_service import hybrid_search_service
from app.services.reranking_service import reranking_service
from app.services.agent_tools import agent_orchestrator
from app.core.config import settings
from typing import Optional
import uuid
import sys
from pathlib import Path

# Add data_pipeline to path for database access
sys.path.append(str(Path(__file__).parent.parent.parent))
from data_pipeline.product_database import product_db

router = APIRouter(prefix="/api/shopping", tags=["shopping"])

# Session storage (use Redis in production)
sessions = {}

# Market name mapping: frontend ID -> database name
MARKET_MAPPING = {
    "el_mazraa": "Mazraa Market",
    "aziza": "aziza",  # Match database exactly (lowercase)
    "carrefour": "Carrefour",
    "mg": "MG",
    "geant": "Géant",
    "monoprix": "Monoprix"
}

def get_db_market_name(frontend_market: str) -> str:
    """Convert frontend market ID to database market name"""
    return MARKET_MAPPING.get(frontend_market, frontend_market)

@router.post("/search-by-image")
async def search_by_image(
    image: UploadFile = File(...),
    market: str = Form(...),
    budget: float = Form(...),
    session_id: Optional[str] = Form(None),
    text_hint: Optional[str] = Form(None),  # Optional: product name hint
    limit: int = Form(1)  # Default to 1 for exact match
):
    """
    MODE B: Shopping Mode - Image-based product search with optional text hint
    
    Returns the BEST MATCH product with clear budget status.
    
    Optional text_hint improves accuracy (e.g., "yaourt", "lait", brand name)
    """
    try:
        # Read image first
        image_bytes = await image.read()
        
        # Map frontend market ID to database market name
        db_market = get_db_market_name(market)
        print(f"\n🔍 Shopping Mode Search")
        print(f"  Frontend Market: {market}")
        print(f"  Database Market: {db_market}")
        print(f"  Budget: {budget} TND")
        print(f"  Image size: {len(image_bytes)} bytes")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create cart if doesn't exist
        if session_id not in sessions:
            cart = cart_service.create_cart(session_id, budget)
            sessions[session_id] = {"cart": cart, "market": db_market}
        
        # Check cache for search results first
        cached_results = cache_service.get_search_results(
            image_bytes, db_market, budget, limit
        )
        
        if cached_results:
            print("  [CACHE] Using cached search results")
            
            # Get the best match - handle both old and new cache formats
            if cached_results:
                best_match = cached_results[0]
                
                # Check if it's old format (with "product" wrapper) or new format (direct payload)
                if "product" in best_match and "payload" in best_match["product"]:
                    # Old format from Groq ranking
                    payload = best_match["product"]["payload"]
                    similarity_score = best_match.get("similarity_score", 0.5)
                else:
                    # New format (direct from Qdrant)
                    payload = best_match.get("payload", best_match)
                    similarity_score = best_match.get("score", 0.5)
                
                # Check budget status
                product_price = payload["price"]
                within_budget = product_price <= budget
                budget_status = "Within budget" if within_budget else f"Over budget by {product_price - budget:.2f} TND"
                
                return {
                    "session_id": session_id,
                    "market": market,
                    "budget": budget,
                    "product": {
                        "id": payload["product_id"],
                        "name": payload["name"],
                        "description": payload["description"],
                        "price": product_price,
                        "market": payload["market"],
                        "brand": payload.get("brand"),
                        "image_url": payload.get("image_path")
                    },
                    "match_confidence": similarity_score,
                    "within_budget": within_budget,
                    "budget_status": budget_status,
                    "cart": cart_service.get_cart(session_id),
                    "cached": True
                }
        
        # Check cache for embedding
        cached_result = cache_service.get_embedding(image_bytes)
        
        if cached_result is None:
            # Generate visual embedding with optional BLIP caption
            print("  ⏳ Generating SigLIP embedding + BLIP caption...")
            result = hybrid_embedding_service.create_query_embedding(
                image_bytes=image_bytes,
                ocr_text=None,
                use_vlm=True  # Enable BLIP for better context
            )
            
            image_embedding = result["embedding"]
            text_hint = result["combined_text"]  # BLIP caption
            
            # Cache the result
            cache_service.set_embedding(image_bytes, image_embedding)
        else:
            image_embedding = cached_result
            text_hint = None
        
        # AGENTIC RAG: Use agent orchestrator for multi-step reasoning
        print("  [AGENT] Activating Agentic RAG workflow...")
        
        agent_result = agent_orchestrator.execute_workflow(
            query_vector=image_embedding,
            query_text=text_hint,
            market=db_market,
            budget=budget,
            limit=10
        )
        
        if not agent_result["success"]:
            print(f"  [WARNING] Agent workflow failed: {agent_result.get('message')}")
            
            # Map database market name to display name
            market_display_name = {
                "Carrefour": "Carrefour",
                "Mazraa Market": "Mazraa Market", 
                "aziza": "Aziza"
            }.get(db_market, db_market)
            
            return {
                "session_id": session_id,
                "market": market,
                "budget": budget,
                "product_not_found": True,
                "status": "no_products_in_market",
                "message": f"No products found in {market_display_name}",
                "suggestion": f"Try searching in a different market or check if this product is available.",
                "cart": cart_service.get_cart(session_id),
                "cached": False
            }
        
        # Extract results from agent workflow
        market_results = [agent_result["best_match"]]
        all_markets_results = []  # Agent already found alternatives
        
        # Get alternatives from agent
        agent_alternatives = agent_result.get("alternatives", [])
        
        print(f"  [OK] Agent completed workflow with {len(agent_result.get('reasoning_chain', []))} steps")
        print(f"  [INFO] Agent reasoning: {' -> '.join(agent_result.get('reasoning_chain', []))}")
        
        if not market_results:
            # No results found in Qdrant (fallback case)
            market_display_name = {
                "Carrefour": "Carrefour",
                "Mazraa Market": "Mazraa Market",
                "aziza": "Aziza"
            }.get(db_market, db_market)
            
            return {
                "session_id": session_id,
                "market": market,
                "budget": budget,
                "product_not_found": True,
                "status": "no_products_in_market",
                "message": f"No products found in {market_display_name}",
                "suggestion": f"Try searching in a different market or check if this product is available.",
                "cart": cart_service.get_cart(session_id),
                "cached": False
            }
        
        print(f"  [OK] Found {len(market_results)} products in {market}")
        
        # RE-RANK results using multiple signals for better accuracy
        print("  [RERANK] Re-ranking results with multiple signals...")
        market_results = reranking_service.rerank(
            results=market_results,
            ocr_text=text_hint
        )
        
        # PROTOTYPE-BASED BOOSTING (Few-Shot Learning)
        # Boost scores based on prototype similarity
        if prototype_service.prototypes:
            print("  [PROTOTYPE] Applying prototype-based boosting...")
            for result in market_results:
                payload = result["payload"]
                base_score = result.get("final_score", result.get("score", 0))
                
                # Boost if matches closest prototype
                boosted_score = prototype_service.boost_score_by_prototype(
                    query_embedding=image_embedding,
                    product_category=payload.get("category", "unknown"),
                    product_brand=payload.get("brand", "unknown"),
                    base_score=base_score
                )
                
                result["final_score"] = boosted_score
            
            # Re-sort after boosting
            market_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # Get the BEST MATCH after re-ranking
        best_match = market_results[0]
        payload = best_match["payload"]
        product_price = payload["price"]
        similarity_score = best_match.get("final_score", best_match.get("score", 0))
        
        # 🚨 DUAL-THRESHOLD EVALUATION
        # Retail-grade thresholds:
        # - Exact match (same brand & product): 82%+
        # - Similar product (same category): 65-82%
        # - Not found: <65%
        EXACT_MATCH_THRESHOLD = 0.82  # 82% for exact match
        SIMILAR_MATCH_THRESHOLD = 0.65  # 65% for similar product (lowered for small dataset)
        
        if similarity_score < SIMILAR_MATCH_THRESHOLD:
            # Below 65% - definitely not found
            print(f"  [WARNING] Very low confidence: {similarity_score*100:.0f}% < {SIMILAR_MATCH_THRESHOLD*100:.0f}%")
            print(f"  [ERROR] Product not found in {market}")
            print(f"  [INFO] Closest match was: {payload['name']} ({similarity_score*100:.0f}%)")  # Debug info
            
            # Map database market name to display name
            market_display_name = {
                "Carrefour": "Carrefour",
                "Mazraa Market": "Mazraa Market",
                "aziza": "Aziza"
            }.get(db_market, db_market)
            
            # Detect category and brand from OCR text
            detected_category = "product"
            detected_brand = "unknown"
            
            if text_hint:
                # Simple category detection
                text_lower = text_hint.lower()
                if any(word in text_lower for word in ['yaourt', 'yogurt', 'yog']):
                    detected_category = "yogurt"
                elif any(word in text_lower for word in ['lait', 'milk', 'lben']):
                    detected_category = "milk"
                elif any(word in text_lower for word in ['fromage', 'cheese', 'jben']):
                    detected_category = "cheese"
                elif any(word in text_lower for word in ['jus', 'juice']):
                    detected_category = "juice"
                elif any(word in text_lower for word in ['eau', 'water']):
                    detected_category = "water"
                elif any(word in text_lower for word in ['huile', 'oil']):
                    detected_category = "hair oil"
                elif any(word in text_lower for word in ['savon', 'soap']):
                    detected_category = "soap"
                elif any(word in text_lower for word in ['shampoo', 'shampoing']):
                    detected_category = "shampoo"
                
                # Extract brand if present
                brands = ['danone', 'delice', 'vitalait', 'yab', 'lilas', 'vidal', 'garnier', 'loreal']
                for brand in brands:
                    if brand in text_lower:
                        detected_brand = brand.title()
                        break
            
            return {
                "session_id": session_id,
                "market": market,
                "budget": budget,
                "product_not_found": True,
                "status": "unknown_product",
                "detected_category": detected_category,
                "detected_brand": detected_brand,
                "message": f"Product not found in {market_display_name}",
                "suggestion": f"We detected a {detected_category}" + (f" from {detected_brand}" if detected_brand != "unknown" else "") + ", but it's not in our database. Try searching in a different market.",
                "cart": cart_service.get_cart(session_id),
                "cached": False
            }
        
        elif similarity_score < EXACT_MATCH_THRESHOLD:
            # 70-82% - Similar product (different brand or variant)
            print(f"  [WARNING] Similar match: {similarity_score*100:.0f}% (not exact)")
            print(f"  [INFO] Showing similar product as suggestion")
            
            # Mark as similar, not exact
            is_similar = True
        else:
            # 82%+ - Exact match
            print(f"  [OK] Exact match: {similarity_score*100:.0f}% >= {EXACT_MATCH_THRESHOLD*100:.0f}%")
            is_similar = False
        
        # Check budget status
        within_budget = product_price <= budget
        budget_status = "Within budget" if within_budget else f"Over budget by {product_price - budget:.2f} TND"
        
        # Cache the result
        cache_service.set_search_results(
            image_bytes, market, budget, limit, [best_match]
        )
        
        print(f"  [MATCH] Best match: {payload['name']} ({similarity_score*100:.0f}% match)")
        print(f"  [PRICE] Price: {product_price} TND - {budget_status}")
        
        # Use agent's analysis and recommendations
        recommendation = None
        alternatives = []
        suggested_quantity = 1
        quantity_reasoning = "single unit"
        total_price = product_price
        total_within_budget = within_budget
        
        try:
            # Get quantity suggestion from agent
            if agent_result.get("quantity_suggestion"):
                qty_data = agent_result["quantity_suggestion"]
                suggested_quantity = qty_data["quantity"]
                quantity_reasoning = qty_data["reasoning"]
                total_price = qty_data["total_price"]
                total_within_budget = qty_data["within_budget"]
                print(f"  [QUANTITY] Agent suggested: {suggested_quantity}x ({quantity_reasoning})")
            
            # Get alternatives from agent
            if agent_result.get("alternatives"):
                for alt in agent_result["alternatives"]:
                    alt_product = alt["product"].get("payload", alt["product"])
                    alternatives.append({
                        "product": {
                            "id": alt_product["product_id"],
                            "name": alt_product["name"],
                            "price": alt_product["price"],
                            "market": alt_product["market"],
                            "brand": alt_product.get("brand"),
                            "description": alt_product.get("description")
                        },
                        "savings": round(alt["savings"], 2),
                        "percentage_cheaper": round(alt["percentage"], 1),
                        "similarity_score": alt.get("similarity", 0)
                    })
                print(f"  [ALTERNATIVES] Agent found {len(alternatives)} cheaper alternative(s)")
            
            # Use agent's recommendation or generate with Groq
            if agent_result.get("recommendation"):
                recommendation = agent_result["recommendation"]
                print(f"  [RECOMMENDATION] Agent recommendation: {recommendation}")
            else:
                # Fallback to Groq for natural language recommendation
                print("  [GROQ] Generating Groq recommendation...")
                
                budget_status_text = "Within budget" if within_budget else f"Over budget by {product_price - budget:.2f} TND"
                
                alternatives_text = "No cheaper alternatives found - this is the best price!"
                if alternatives:
                    alt_lines = []
                    for alt in alternatives:
                        alt_line = f"- {alt['product']['name']} at {alt['product']['market']} for {alt['product']['price']} TND (save {alt['savings']} TND, {alt['percentage_cheaper']:.0f}% cheaper)"
                        alt_lines.append(alt_line)
                    alternatives_text = "Cheaper Alternatives Found:\n" + "\n".join(alt_lines)
                
                groq_prompt = f"""You are a shopping assistant. A user found this product:

Product: {payload['name']}
Unit Price: {product_price} TND
Suggested Quantity: {suggested_quantity} ({quantity_reasoning})
Total Price: {total_price:.2f} TND
Market: {market}
User's Budget: {budget} TND
Match Confidence: {similarity_score*100:.0f}%

Budget Status: {budget_status_text}

{alternatives_text}

Provide a brief recommendation (2-3 sentences):
1. Mention the suggested quantity and why (e.g., "Get {suggested_quantity} for {total_price:.2f} TND")
2. Should they add it to cart or switch markets?
3. Mention budget status and cheaper alternatives if available

Be friendly and helpful. Keep it short."""

                from openai import OpenAI
                client = OpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url=settings.GROQ_BASE_URL
                )
                
                response = client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful shopping assistant. Be brief and friendly."},
                        {"role": "user", "content": groq_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                recommendation = response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"  [WARNING] Could not generate recommendation: {e}")
            # Fallback recommendation
            if within_budget:
                recommendation = f"This product is within your budget. You can add it to your cart!"
            else:
                recommendation = f"This product is over your budget by {product_price - budget:.2f} TND. Consider looking for alternatives."
        
        return {
            "session_id": session_id,
            "market": market,
            "budget": budget,
            "product": {
                "id": payload["product_id"],
                "name": payload["name"],
                "description": payload["description"],
                "price": product_price,
                "market": payload["market"],
                "brand": payload.get("brand"),
                "image_url": payload.get("image_path")
            },
            "quantity_suggestion": {
                "quantity": suggested_quantity,
                "reasoning": quantity_reasoning,
                "unit_price": product_price,
                "total_price": total_price,
                "within_budget": total_within_budget
            },
            "match_confidence": similarity_score,
            "is_similar_match": is_similar,  # True if 70-82%, False if 82%+
            "match_type": "similar" if is_similar else "exact",
            "within_budget": within_budget,
            "budget_status": budget_status,
            "recommendation": recommendation,
            "alternatives": alternatives,
            "cart": cart_service.get_cart(session_id),
            "cached": False
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

@router.post("/cart/add")
async def add_to_cart(
    session_id: str = Form(...),
    product_id: str = Form(...),
    product_name: str = Form(...),
    product_price: float = Form(...),
    product_market: str = Form(...),
    product_description: str = Form(None),
    quantity: int = Form(1)
):
    """Add product to virtual cart with tax calculation"""
    try:
        cart = cart_service.get_cart(session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        # Create product from form data
        product = Product(
            id=product_id,
            name=product_name,
            description=product_description or "",
            category="food",
            price=product_price,
            market=product_market
        )
        
        # Add to cart with market for tax calculation
        result = cart_service.add_item(session_id, product, quantity, product_market)
        updated_cart = result["cart"]
        
        # Calculate tax info
        tax_info = ""
        if product_market.lower() == 'aziza' and len(updated_cart.items) > 0:
            tax_info = f" (includes 0.10 TND shopping fee)"
        
        message = f"[OK] Added {quantity}x {product_name} to cart{tax_info}"
        
        if updated_cart.is_over_budget:
            message = f"[WARNING] Cart is over budget by {updated_cart.overspend_amount:.2f} TND"
        
        return {
            "cart": updated_cart,
            "message": message,
            "success": True
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to add to cart: {str(e)}")

@router.get("/cart/{session_id}", response_model=CartResponse)
async def get_cart(session_id: str):
    """Get current cart"""
    cart = cart_service.get_cart(session_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    message = "Cart retrieved successfully"
    if cart.is_over_budget:
        message = f"[WARNING] Cart is over budget by {cart.overspend_amount:.2f} TND"
    
    return CartResponse(
        cart=cart,
        suggestions=[],
        message=message
    )

@router.delete("/cart/{session_id}/item/{product_id}")
async def remove_from_cart(session_id: str, product_id: str, market: str = None):
    """Remove item completely from cart"""
    try:
        updated_cart = cart_service.remove_item(session_id, product_id, market)
        return CartResponse(
            cart=updated_cart,
            suggestions=[],
            message=f"Item removed from cart"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/cart/{session_id}/item/{product_id}/quantity")
async def update_item_quantity(
    session_id: str,
    product_id: str,
    quantity: int = Form(...),
    market: str = Form(None)
):
    """Update item quantity (set exact quantity)"""
    try:
        if quantity < 0:
            raise HTTPException(status_code=400, detail="Quantity cannot be negative")
        
        updated_cart = cart_service.set_item_quantity(session_id, product_id, quantity, market)
        
        message = f"Quantity updated to {quantity}"
        if quantity == 0:
            message = "Item removed from cart"
        
        if updated_cart.is_over_budget:
            message = f"[WARNING] Cart is over budget by {updated_cart.overspend_amount:.2f} TND"
        
        return CartResponse(
            cart=updated_cart,
            suggestions=[],
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cart/{session_id}/item/{product_id}/increase")
async def increase_item_quantity(
    session_id: str,
    product_id: str,
    amount: int = Form(1),
    market: str = Form(None)
):
    """Increase item quantity by specified amount"""
    try:
        # Get current item
        cart = cart_service.get_cart(session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        item = next((item for item in cart.items if item.product.id == product_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Item not in cart")
        
        # Increase quantity
        new_quantity = item.quantity + amount
        updated_cart = cart_service.set_item_quantity(session_id, product_id, new_quantity, market)
        
        message = f"[OK] Increased to {new_quantity}x"
        if updated_cart.is_over_budget:
            message = f"[WARNING] Cart is over budget by {updated_cart.overspend_amount:.2f} TND"
        
        return CartResponse(
            cart=updated_cart,
            suggestions=[],
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cart/{session_id}/item/{product_id}/decrease")
async def decrease_item_quantity(
    session_id: str,
    product_id: str,
    amount: int = Form(1),
    market: str = Form(None)
):
    """Decrease item quantity by specified amount"""
    try:
        updated_cart = cart_service.decrease_quantity(session_id, product_id, amount, market)
        
        # Check if item still exists
        item = next((item for item in updated_cart.items if item.product.id == product_id), None)
        
        if item:
            message = f"[OK] Decreased to {item.quantity}x"
        else:
            message = "Item removed from cart (quantity reached 0)"
        
        return CartResponse(
            cart=updated_cart,
            suggestions=[],
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cart/{session_id}/clear")
async def clear_cart(session_id: str):
    """Clear all items from cart"""
    try:
        updated_cart = cart_service.clear_cart(session_id)
        return CartResponse(
            cart=updated_cart,
            suggestions=[],
            message="Cart cleared"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/markets")
async def get_markets():
    """Get list of available supermarkets"""
    # Get actual markets from database
    db_stats = product_db.get_statistics()
    markets_in_db = db_stats.get('by_market', {})
    
    all_markets = [
        {"id": "aziza", "name": "Aziza", "logo": "/logos/aziza.png", "products": markets_in_db.get("aziza", 0)},
        {"id": "carrefour", "name": "Carrefour", "logo": "/logos/carrefour.png", "products": markets_in_db.get("carrefour", 0)},
        {"id": "mg", "name": "MG", "logo": "/logos/mg.png", "products": markets_in_db.get("mg", 0)},
        {"id": "geant", "name": "Géant", "logo": "/logos/geant.png", "products": markets_in_db.get("geant", 0)},
        {"id": "monoprix", "name": "Monoprix", "logo": "/logos/monoprix.png", "products": markets_in_db.get("monoprix", 0)},
        {"id": "el_mazraa", "name": "El Mazraa", "logo": "/logos/el_mazraa.png", "products": markets_in_db.get("el_mazraa", 0)}
    ]
    
    return {"markets": all_markets}

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    cache_stats = cache_service.get_stats()
    db_stats = product_db.get_statistics()
    
    return {
        "cache": cache_stats,
        "database": {
            "total_products": db_stats['total_products'],
            "by_market": db_stats['by_market'],
            "products_with_promos": db_stats['products_with_promos']
        }
    }

@router.post("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    cache_service.clear_all()
    return {"message": "Cache cleared successfully"}

@router.post("/cache/clear-expired")
async def clear_expired_cache():
    """Clear expired cache entries"""
    cache_service.clear_expired()
    stats = cache_service.get_stats()
    return {
        "message": "Expired cache entries cleared",
        "remaining_entries": stats['total_entries']
    }

@router.get("/price-comparison/{product_name}")
async def compare_prices(
    product_name: str,
    current_market: str,
    current_price: float,
    limit: int = 5
):
    """
    Compare prices for a product across all supermarkets.
    Find cheaper alternatives in other markets.
    """
    try:
        comparison = price_comparison_service.get_price_comparison_summary(
            product_name=product_name,
            current_market=current_market,
            current_price=current_price,
            limit=limit
        )
        
        return comparison
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price comparison failed: {str(e)}")

@router.post("/find-best-deal")
async def find_best_deal(
    product_name: str = Form(...),
    current_market: str = Form(...),
    current_price: float = Form(...)
):
    """
    Find the best deal (cheapest option) for a specific product.
    Returns the cheapest alternative or None if current is best.
    """
    try:
        best_deal = price_comparison_service.get_best_deal(
            product_name=product_name,
            current_market=current_market,
            current_price=current_price
        )
        
        if best_deal:
            return {
                "has_better_deal": True,
                "best_deal": best_deal,
                "message": f"Found cheaper option in {best_deal['market']}: {best_deal['savings']:.2f} TND savings"
            }
        else:
            return {
                "has_better_deal": False,
                "message": f"{current_market} already has the best price"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Best deal search failed: {str(e)}")


@router.get("/cart/analysis/{session_id}")
async def get_cart_analysis(session_id: str):
    """
    Get comprehensive cart analysis with explainable AI insights
    
    Returns:
        - Budget status with clear explanations
        - Shopping summary with insights
        - Recommendations based on spending
    """
    try:
        analysis = cart_service.get_cart_analysis(session_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/cart/check-item-impact")
async def check_item_impact(
    session_id: str = Form(...),
    product_id: str = Form(...),
    quantity: int = Form(1)
):
    """
    Check the impact of adding an item before actually adding it
    
    Returns:
        - Whether item can be added
        - Impact on budget
        - Clear explanation and suggestions
    """
    try:
        from app.services.explainable_ai_service import explainable_ai_service
        
        cart = cart_service.get_cart(session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        # Get product from database
        db_product = product_db.get_product_by_id(int(product_id))
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Convert to Product schema
        product = Product(
            id=str(db_product['product_id']),
            name=db_product['name'],
            description=db_product['description'],
            category=db_product['category'],
            price=db_product['price'],
            market=db_product['market'],
            image_path=db_product.get('image_url'),
            specs=None,
            brand=db_product.get('brand')
        )
        
        # Analyze impact
        impact = explainable_ai_service.explain_item_impact(cart, product, quantity)
        
        return impact
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impact check failed: {str(e)}")


@router.post("/cart/get-optimization")
async def get_optimization_suggestions(
    session_id: str = Form(...)
):
    """
    Get AI-powered optimization suggestions with clear explanations
    
    Returns:
        - Budget status
        - Smart alternatives (remove, replace, reduce quantity)
        - Clear explanations for each suggestion
    """
    try:
        # Get all products for alternatives
        all_products_db = product_db.get_all_products(limit=1000)
        
        # Convert to Product schema
        all_products = []
        for db_prod in all_products_db:
            product = Product(
                id=str(db_prod['product_id']),
                name=db_prod['name'],
                description=db_prod['description'],
                category=db_prod['category'],
                price=db_prod['price'],
                market=db_prod['market'],
                image_path=db_prod.get('image_url'),
                specs=None,
                brand=db_prod.get('brand')
            )
            all_products.append(product)
        
        # Get optimization suggestions
        optimization = await cart_service.get_optimization_suggestions(
            session_id,
            all_products
        )
        
        return optimization
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/cart/budget-status/{session_id}")
async def get_budget_status(session_id: str):
    """
    Get detailed budget status with explanations
    
    Returns:
        - Status: safe, warning, or over
        - Percentage used
        - Clear explanation
        - Actionable recommendations
    """
    try:
        from app.services.explainable_ai_service import explainable_ai_service
        
        cart = cart_service.get_cart(session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        budget_status = explainable_ai_service.analyze_budget_status(cart)
        
        return budget_status
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Budget status check failed: {str(e)}")
