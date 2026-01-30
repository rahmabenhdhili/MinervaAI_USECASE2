#!/usr/bin/env python3
"""
🚀 UNIFIED MAIN APPLICATION - MinervaAI/Dinero Platform
Combines all applications into a single FastAPI server

Applications:
1. B2C Marketplace (/api/b2c/*) - Product scraping, marketplace, orders
2. B2B Supplier Search (/api/b2b/*) - Supplier search with personalization
3. Usershop Recommendations (/api/usershop/*) - CSV-based product recommendations
4. ShopGPT (/api/shopgpt/*) - Image-based shopping assistant

Usage:
    python main_unified.py              # Start all services
    python main_unified.py --help       # Show help
"""

import sys
import os
from contextlib import asynccontextmanager
from typing import Optional, List

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import tempfile
from datetime import datetime

# ==================== IMPORTS FOR B2C ====================
from models import SearchQuery, RecommendationResponse
from services.recommendation_service import RecommendationService
from services.realtime_semantic_search_service import RealtimeSemanticSearchService
from services.marketing_service import MarketingService
from services.marketplace_service import MarketplaceService
from services.order_service import OrderService
from services.settings_service import SettingsService
from config import get_settings

# ==================== IMPORTS FOR B2B ====================
from app.routes import auth, home, search_proxy, click
from app.database_sqlite import get_events_collection
from app.core.security import get_current_user_id

# Check if B2B scripts exist
try:
    from scripts.embedding_agent_B2B import EmbeddingAgent
    from scripts.qroq_explainerB2B import GroqExplainer
    from scripts.search_B2B import SemanticSearchAgent
    from scripts.price_optimizeB2B import PriceOptimizer
    B2B_AVAILABLE = True
except ImportError:
    B2B_AVAILABLE = False
    print("⚠️ B2B scripts not found - B2B endpoints will be disabled")

# ==================== IMPORTS FOR USERSHOP ====================
from app.config_usershop import settings as usershop_settings
from app.models_usershop import (
    Product, 
    RecommendationRequest, 
    RecommendationResponse as UsershopRecommendationResponse,
    ProductSearchRequest,
    ProductComparisonRequest,
    ComparisonResponse
)
from app.database_usershop import db as usershop_db
from app.llm_service_v2_usershop import advanced_llm_service
from app.data_loader_usershop import data_loader

# ==================== IMPORTS FOR SHOPGPT ====================
try:
    from app.core.config import settings as shopgpt_settings
    from app.api import shopping
    SHOPGPT_AVAILABLE = True
except ImportError as e:
    SHOPGPT_AVAILABLE = False
    print(f"⚠️ ShopGPT modules not found - ShopGPT endpoints will be disabled")
except Exception as e:
    SHOPGPT_AVAILABLE = False
    print(f"⚠️ ShopGPT initialization error - ShopGPT endpoints will be disabled: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== GLOBAL SERVICES ====================
# B2C Services
recommendation_service = None
realtime_search_service = None
marketing_service = None
marketplace_service = None
order_service = None
settings_service = None

# B2B Services
b2b_agent = None
b2b_search_agent = None
b2b_price_optimizer = None
b2b_explainer = None

# ==================== PYDANTIC MODELS ====================

# B2C Models
class MarketingRequest(BaseModel):
    product_name: str
    product_description: str

class MarketingResponse(BaseModel):
    product_name: str
    product_description: str
    strategy: str
    success: bool
    error: str = None

class MarketplaceProduct(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    category: str = "general"
    metadata: dict = {}

class MarketplaceProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None

class CreateOrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    shipping_address: dict
    items: List[dict]
    payment_method: str = "card"

class UpdateOrderStatusRequest(BaseModel):
    status: str
    tracking_number: Optional[str] = None
    note: Optional[str] = None

class UpdateSettingsRequest(BaseModel):
    marketplace_name: Optional[str] = None
    marketplace_logo: Optional[str] = None
    marketplace_description: Optional[str] = None

# B2B Models
class SearchRequest(BaseModel):
    product_name: str
    quantity: int = 1
    max_price: float = None

class ClickRequest(BaseModel):
    product_name: str
    brand: str
    category: str
    supplier: str

# ==================== LIFESPAN MANAGEMENT ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services on startup"""
    global recommendation_service, realtime_search_service, marketing_service
    global marketplace_service, order_service, settings_service
    global b2b_agent, b2b_search_agent, b2b_price_optimizer, b2b_explainer
    
    print("=" * 80)
    print("🚀 UNIFIED MINERVA AI PLATFORM - STARTING ALL SERVICES")
    print("=" * 80)
    
    # ==================== INITIALIZE B2C SERVICES ====================
    print("\n📦 [B2C] Initializing B2C Marketplace Services...")
    try:
        recommendation_service = RecommendationService()
        await recommendation_service.initialize()
        realtime_search_service = RealtimeSemanticSearchService()
        marketing_service = MarketingService(debug=True)
        marketplace_service = MarketplaceService(debug=True)
        order_service = OrderService(debug=True)
        settings_service = SettingsService(debug=True)
        print("✅ [B2C] B2C services initialized")
    except Exception as e:
        print(f"❌ [B2C] Error initializing B2C services: {e}")
    
    # ==================== INITIALIZE B2B SERVICES ====================
    if B2B_AVAILABLE:
        print("\n🏭 [B2B] Initializing B2B Supplier Search Services...")
        try:
            b2b_agent = EmbeddingAgent()
            b2b_search_agent = SemanticSearchAgent(b2b_agent)
            b2b_price_optimizer = PriceOptimizer()
            GROQ_API_KEY = os.getenv("GROQ_API_KEY")
            b2b_explainer = GroqExplainer(api_key=GROQ_API_KEY)
            print("✅ [B2B] B2B services initialized")
        except Exception as e:
            print(f"❌ [B2B] Error initializing B2B services: {e}")
    
    # ==================== INITIALIZE USERSHOP SERVICES ====================
    print("\n🛍️ [USERSHOP] Initializing Usershop Recommendation Services...")
    try:
        await usershop_db.initialize_collection()
        collection_info = usershop_db.get_collection_info()
        products_count = collection_info.get('points_count', 0)
        
        if products_count == 0:
            print("📁 [USERSHOP] Loading products from /data directory...")
            possible_paths = ["data", "../data", "../../data"]
            
            for data_path in possible_paths:
                try:
                    products, load_stats = data_loader.load_all_csv_from_directory(data_path)
                    if products:
                        await usershop_db.add_products(products)
                        print(f"✅ [USERSHOP] {len(products)} products loaded from '{data_path}'")
                        break
                except Exception:
                    continue
        else:
            print(f"✅ [USERSHOP] {products_count} products already in Qdrant")
    except Exception as e:
        print(f"⚠️ [USERSHOP] Error initializing Usershop: {e}")
    
    print("\n" + "=" * 80)
    print("✅ ALL SERVICES INITIALIZED SUCCESSFULLY")
    print("=" * 80)
    print("\n📡 Available Services:")
    print("   • B2C Marketplace: /api/b2c/*")
    if B2B_AVAILABLE:
        print("   • B2B Supplier Search: /api/b2b/*")
    print("   • Usershop Recommendations: /api/usershop/*")
    if SHOPGPT_AVAILABLE:
        print("   • ShopGPT Image Search: /api/shopping/*")
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("=" * 80)
    print()
    
    yield
    
    print("\n👋 Shutting down all services...")

# ==================== CREATE FASTAPI APP ====================

settings = get_settings()

app = FastAPI(
    title="MinervaAI Unified Platform",
    description="Unified AI-powered shopping platform with B2C, B2B, and Usershop services",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    """Main entry point showing all available services"""
    services = {
        "b2c": {
            "name": "B2C Marketplace",
            "description": "Product scraping, marketplace management, orders",
            "prefix": "/api/b2c",
            "status": "active"
        },
        "usershop": {
            "name": "Usershop Recommendations",
            "description": "CSV-based product recommendations with AI",
            "prefix": "/api/usershop",
            "status": "active"
        }
    }
    
    if B2B_AVAILABLE:
        services["b2b"] = {
            "name": "B2B Supplier Search",
            "description": "Supplier search with personalization and price optimization",
            "prefix": "/api/b2b",
            "status": "active"
        }
    
    if SHOPGPT_AVAILABLE:
        services["shopgpt"] = {
            "name": "ShopGPT Image Search",
            "description": "Image-based product search with AI",
            "prefix": "/api/shopping",
            "status": "active"
        }
    
    return {
        "platform": "MinervaAI Unified Platform",
        "version": "3.0.0",
        "status": "healthy",
        "services": services,
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check for all services"""
    health_status = {
        "status": "healthy",
        "services": {
            "b2c": "active",
            "usershop": "active"
        }
    }
    
    if B2B_AVAILABLE:
        health_status["services"]["b2b"] = "active"
    
    if SHOPGPT_AVAILABLE:
        health_status["services"]["shopgpt"] = "active"
    
    return health_status


# ==================== B2C ENDPOINTS ====================
# Prefix: /api/b2c

@app.post("/api/b2c/recommend", response_model=RecommendationResponse)
async def b2c_get_recommendations(query: SearchQuery):
    """B2C: Get AI product recommendations with scraping"""
    try:
        if not recommendation_service:
            raise HTTPException(status_code=503, detail="B2C service not initialized")
        
        result = await recommendation_service.get_recommendations(query)
        return result
    except Exception as e:
        logger.error(f"[B2C] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")

@app.post("/api/b2c/search/semantic")
async def b2c_semantic_search(query: SearchQuery):
    """B2C: Real-time semantic search (audit-compliant, ephemeral)"""
    try:
        if not realtime_search_service:
            raise HTTPException(status_code=503, detail="Realtime search service not initialized")
        
        result = await realtime_search_service.search_products_semantic(
            user_query=query.query,
            use_amazon=query.use_amazon,
            use_alibaba=query.use_alibaba,
            use_walmart=query.use_walmart,
            use_cdiscount=query.use_cdiscount,
            max_results=query.max_results,
            top_k=10
        )
        return result
    except Exception as e:
        logger.error(f"[B2C] Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")

@app.post("/api/b2c/marketing", response_model=MarketingResponse)
async def b2c_generate_marketing(request: MarketingRequest):
    """B2C: Generate marketing strategy for a product"""
    try:
        if not marketing_service:
            raise HTTPException(status_code=503, detail="Marketing service not initialized")
        
        result = marketing_service.generate_marketing_strategy(
            product_name=request.product_name,
            product_description=request.product_description
        )
        return MarketingResponse(**result)
    except Exception as e:
        logger.error(f"[B2C] Marketing error: {e}")
        raise HTTPException(status_code=500, detail=f"Marketing error: {str(e)}")

# Marketplace Endpoints
@app.post("/api/b2c/marketplace/products")
async def b2c_add_product(product: MarketplaceProduct):
    """B2C: Add product to user's marketplace"""
    try:
        if not marketplace_service:
            raise HTTPException(status_code=503, detail="Marketplace service not initialized")
        
        result = marketplace_service.add_product(
            name=product.name,
            description=product.description,
            price=product.price,
            image_url=product.image_url,
            category=product.category,
            metadata=product.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[B2C] Add product error: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding product: {str(e)}")

@app.get("/api/b2c/marketplace/products")
async def b2c_get_products():
    """B2C: Get all marketplace products"""
    try:
        if not marketplace_service:
            raise HTTPException(status_code=503, detail="Marketplace service not initialized")
        
        products = marketplace_service.get_all_products()
        return {"success": True, "products": products, "total": len(products)}
    except Exception as e:
        logger.error(f"[B2C] Get products error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@app.get("/api/b2c/marketplace/products/{product_id}")
async def b2c_get_product(product_id: str):
    """B2C: Get specific marketplace product"""
    try:
        if not marketplace_service:
            raise HTTPException(status_code=503, detail="Marketplace service not initialized")
        
        product = marketplace_service.get_product(product_id)
        if product:
            return {"success": True, "product": product}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[B2C] Get product error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@app.put("/api/b2c/marketplace/products/{product_id}")
async def b2c_update_product(product_id: str, product: MarketplaceProductUpdate):
    """B2C: Update marketplace product"""
    try:
        if not marketplace_service:
            raise HTTPException(status_code=503, detail="Marketplace service not initialized")
        
        result = marketplace_service.update_product(
            product_id=product_id,
            name=product.name,
            description=product.description,
            price=product.price,
            image_url=product.image_url,
            category=product.category
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=404 if "non trouvé" in result.get("error", "") else 500,
                detail=result.get("error")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[B2C] Update product error: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@app.delete("/api/b2c/marketplace/products/{product_id}")
async def b2c_delete_product(product_id: str):
    """B2C: Delete marketplace product"""
    try:
        if not marketplace_service:
            raise HTTPException(status_code=503, detail="Marketplace service not initialized")
        
        result = marketplace_service.delete_product(product_id)
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=404 if "non trouvé" in result.get("error", "") else 500,
                detail=result.get("error")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[B2C] Delete product error: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

@app.get("/api/b2c/marketplace/stats")
async def b2c_marketplace_stats():
    """B2C: Get marketplace statistics"""
    try:
        if not marketplace_service:
            raise HTTPException(status_code=503, detail="Marketplace service not initialized")
        
        stats = marketplace_service.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"[B2C] Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

# Order Endpoints
@app.post("/api/b2c/orders")
async def b2c_create_order(order_request: CreateOrderRequest):
    """B2C: Create new order"""
    try:
        if not order_service:
            raise HTTPException(status_code=503, detail="Order service not initialized")
        
        result = order_service.create_order(
            customer_name=order_request.customer_name,
            customer_phone=order_request.customer_phone,
            shipping_address=order_request.shipping_address,
            items=order_request.items,
            payment_method=order_request.payment_method
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[B2C] Create order error: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@app.get("/api/b2c/orders")
async def b2c_get_orders():
    """B2C: Get all orders"""
    try:
        if not order_service:
            raise HTTPException(status_code=503, detail="Order service not initialized")
        
        orders = order_service.get_all_orders()
        return {"success": True, "orders": orders, "total": len(orders)}
    except Exception as e:
        logger.error(f"[B2C] Get orders error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")

@app.get("/api/b2c/orders/stats")
async def b2c_order_stats():
    """B2C: Get order statistics"""
    try:
        if not order_service:
            raise HTTPException(status_code=503, detail="Order service not initialized")
        
        stats = order_service.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"[B2C] Order stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

# Settings Endpoints
@app.get("/api/b2c/settings")
async def b2c_get_settings():
    """B2C: Get marketplace settings"""
    try:
        if not settings_service:
            raise HTTPException(status_code=503, detail="Settings service not initialized")
        
        settings = settings_service.get_settings()
        return {"success": True, "settings": settings}
    except Exception as e:
        logger.error(f"[B2C] Get settings error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching settings: {str(e)}")

@app.put("/api/b2c/settings")
async def b2c_update_settings(settings_request: UpdateSettingsRequest):
    """B2C: Update marketplace settings"""
    try:
        if not settings_service:
            raise HTTPException(status_code=503, detail="Settings service not initialized")
        
        result = settings_service.update_settings(
            marketplace_name=settings_request.marketplace_name,
            marketplace_logo=settings_request.marketplace_logo,
            marketplace_description=settings_request.marketplace_description
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[B2C] Update settings error: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")


# ==================== B2B ENDPOINTS ====================
# Prefix: /api/b2b

# B2B Auth Endpoints
from app.models.user import B2BUserCreate, B2BUserOut, UserCreate
from app.database_sqlite import user_db
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token

@app.post("/api/b2b/auth/register", response_model=B2BUserOut)
async def b2b_register(user: B2BUserCreate):
    """B2B: Register new business user"""
    try:
        hashed_pw = hash_password(user.password)
        user_data = {
            "email": user.email,
            "password": hashed_pw,
            "company_name": user.company_name,
            "contact_person": user.contact_person,
            "phone": user.phone,
            "address": user.address,
            "business_type": user.business_type,
            "user_type": "b2b",
            "is_verified": False
        }
        
        created_user = user_db.create_user(user_data)
        
        return B2BUserOut(
            id=created_user["id"],
            email=created_user["email"],
            company_name=created_user["company_name"],
            contact_person=created_user["contact_person"],
            phone=created_user["phone"],
            address=created_user["address"],
            business_type=created_user["business_type"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[B2B] Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/b2b/auth/login")
async def b2b_login(user: UserCreate):
    """B2B: Login business user"""
    try:
        db_user = user_db.get_user_by_email(user.email, user_type="b2b")
        if not db_user or not verify_password(user.password, db_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": db_user["id"]})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": B2BUserOut(
                id=db_user["id"],
                email=db_user["email"],
                company_name=db_user["company_name"],
                contact_person=db_user["contact_person"],
                phone=db_user["phone"],
                address=db_user["address"],
                business_type=db_user["business_type"]
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[B2B] Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/b2b/auth/stats")
async def b2b_auth_stats():
    """B2B: Get user registration statistics"""
    try:
        stats = user_db.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"[B2B] Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

if B2B_AVAILABLE:
    @app.post("/api/b2b/search")
    async def b2b_search_suppliers(
        req: SearchRequest,
        user_id: str = Depends(get_current_user_id)
    ):
        """B2B: Search for best suppliers with price optimization"""
        try:
            # Log search event
            events = get_events_collection()
            event_id = events.track_event({
                "user_id": user_id,
                "event_type": "search",
                "content": req.product_name
            })
            
            # Search suppliers
            products = b2b_search_agent.search(req.product_name, top_k=20)
            
            # Optimize by price
            optimized_products = b2b_price_optimizer.optimize(
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
            
            best_supplier = optimized_products[0]
            alternatives = [
                p for p in optimized_products[1:]
                if p["total_price"] > best_supplier["total_price"]
                and (req.max_price is None or p["total_price"] <= req.max_price)
            ][:3]
            
            explanation = b2b_explainer.explain_choice(
                best_supplier=best_supplier,
                query=req.product_name,
                quantity=req.quantity
            )
            
            return {
                "best_product": best_supplier,
                "alternatives": alternatives,
                "explanation": explanation
            }
        except Exception as e:
            logger.error(f"[B2B] Search error: {e}")
            raise HTTPException(status_code=500, detail=f"B2B search error: {str(e)}")
    
    @app.post("/api/b2b/click")
    async def b2b_track_click(
        req: ClickRequest,
        user_id: str = Depends(get_current_user_id)
    ):
        """B2B: Track user click for personalization"""
        try:
            events = get_events_collection()
            event_id = events.track_event({
                "user_id": user_id,
                "event_type": "click",
                "content": req.product_name
            })
            return {"status": "ok", "message": "Click recorded", "event_id": event_id}
        except Exception as e:
            logger.error(f"[B2B] Click tracking error: {e}")
            raise HTTPException(status_code=500, detail=f"Click tracking error: {str(e)}")
    
    @app.get("/api/b2b/recommendations")
    async def b2b_get_recommendations(
        user_id: str = Depends(get_current_user_id)
    ):
        """B2B: Get personalized supplier recommendations"""
        try:
            from app.core.personalization import get_user_preference_text
            from app.core.qdrant_personalization import query_personalized_products
            
            # Get user preferences from their interaction history
            preference_text = await get_user_preference_text(user_id)
            
            if not preference_text:
                return {
                    "recommended_products": [],
                    "reason": "No search history yet. Start searching to get personalized recommendations!"
                }
            
            # Query personalized products based on user preferences
            products = query_personalized_products(preference_text, top_k=10)
            
            # Add additional fields for frontend compatibility
            for product in products:
                if not product.get('description'):
                    product['description'] = f"Recommended based on your interest in {product.get('category', 'similar products')}"
                if not product.get('phone'):
                    product['phone'] = None
                if not product.get('email'):
                    product['email'] = None
                if not product.get('city'):
                    product['city'] = None
            
            return {
                "recommended_products": products,
                "reason": "Based on your search history and clicked suppliers",
                "total_count": len(products)
            }
            
        except Exception as e:
            logger.error(f"[B2B] Recommendations error: {e}")
            raise HTTPException(status_code=500, detail=f"Recommendations error: {str(e)}")
    
    # Include B2B auth routes
    app.include_router(auth.router, prefix="/api/b2b", tags=["B2B Auth"])
    app.include_router(home.router, prefix="/api/b2b", tags=["B2B Home"])
    app.include_router(search_proxy.router, prefix="/api/b2b", tags=["B2B Search Proxy"])
    app.include_router(click.router, prefix="/api/b2b", tags=["B2B Click"])

# ==================== USERSHOP ENDPOINTS ====================
# Prefix: /api/usershop

@app.post("/api/usershop/recommend", response_model=UsershopRecommendationResponse)
async def usershop_get_recommendations(request: RecommendationRequest):
    """Usershop: Get ultra-precise product recommendations"""
    try:
        logger.info(f"[USERSHOP] New search: {request.dict()}")
        
        # Create search query
        search_query = advanced_llm_service.create_search_query(request.dict())
        
        # Vector search (100 products)
        search_limit = 100
        similar_products = await usershop_db.search_similar_products(search_query, limit=search_limit)
        
        if not similar_products:
            raise HTTPException(status_code=404, detail="No products found")
        
        total_found = len(similar_products)
        
        # Advanced filtering and scoring
        best_products = advanced_llm_service.select_best_products(
            similar_products, 
            request.dict(), 
            limit=request.limit
        )
        
        if not best_products:
            raise HTTPException(status_code=404, detail="No products match price criteria")
        
        total_after_filter = len(best_products)
        target_product = best_products[0]
        
        # Generate recommendations with AI
        recommendations = await advanced_llm_service.generate_recommendations(
            target_product, 
            best_products[1:],
            request.dict(),
            total_found,
            total_after_filter
        )
        
        logger.info(f"[USERSHOP] Recommendations generated: 1 main + {len(recommendations.recommendations)} similar")
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USERSHOP] Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/api/usershop/compare", response_model=ComparisonResponse)
async def usershop_compare_products(request: ProductComparisonRequest):
    """Usershop: Compare two products with AI analysis"""
    try:
        logger.info(f"[USERSHOP] Comparison: {request.product_id_1} vs {request.product_id_2}")
        
        product_1 = await usershop_db.get_product_by_id(request.product_id_1)
        product_2 = await usershop_db.get_product_by_id(request.product_id_2)
        
        if not product_1:
            raise HTTPException(status_code=404, detail=f"Product 1 not found: {request.product_id_1}")
        
        if not product_2:
            raise HTTPException(status_code=404, detail=f"Product 2 not found: {request.product_id_2}")
        
        comparison_data = await advanced_llm_service.compare_products(product_1, product_2)
        response = ComparisonResponse(**comparison_data)
        
        logger.info(f"[USERSHOP] Comparison generated: {response.final_recommendation}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USERSHOP] Comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/usershop/product/{product_id}")
async def usershop_get_product(product_id: str):
    """Usershop: Get product details by ID"""
    try:
        product = await usershop_db.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USERSHOP] Get product error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/usershop/search")
async def usershop_search_products(request: ProductSearchRequest):
    """Usershop: Search products by text query"""
    try:
        products = await usershop_db.search_similar_products(request.query, request.limit)
        return {"query": request.query, "results": products, "count": len(products)}
    except Exception as e:
        logger.error(f"[USERSHOP] Search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/usershop/add-products")
async def usershop_add_products(file: UploadFile = File(...)):
    """Usershop: Upload CSV file with products"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            if not data_loader.validate_csv_format(tmp_file_path):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid CSV format. Required columns: url, name, category, brand, img, description, price"
                )
            
            products, load_stats = data_loader.load_products_from_csv(tmp_file_path)
            
            if not products:
                raise HTTPException(status_code=400, detail="No valid products found in CSV")
            
            upload_stats = await usershop_db.add_products(products)
            
            return {
                "message": f"{len(products)} products added successfully",
                "count": len(products),
                "loading_stats": load_stats,
                "upload_stats": upload_stats,
                "all_steps": load_stats["steps"] + upload_stats["steps"]
            }
        finally:
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USERSHOP] Add products error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/api/usershop/load-from-directory")
async def usershop_load_directory(directory: str = "data"):
    """Usershop: Load all CSV files from directory"""
    try:
        logger.info(f"[USERSHOP] Loading products from '{directory}'...")
        
        products, load_stats = data_loader.load_all_csv_from_directory(directory)
        
        if not products:
            raise HTTPException(status_code=404, detail=f"No products found in '{directory}'")
        
        upload_stats = await usershop_db.add_products(products)
        collection_info = usershop_db.get_collection_info()
        
        return {
            "message": f"✅ {len(products)} products loaded from {load_stats['files_processed']} file(s)",
            "total_products": len(products),
            "files_processed": load_stats['files_processed'],
            "collection_info": collection_info,
            "loading_stats": load_stats,
            "upload_stats": upload_stats,
            "all_steps": load_stats["steps"] + upload_stats["steps"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USERSHOP] Load directory error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/usershop/stats")
async def usershop_get_stats():
    """Usershop: Get database statistics"""
    try:
        collection_info = usershop_db.get_collection_info()
        return {
            "status": "ok",
            "service": "usershop",
            "collection": collection_info,
            "embedding_model": usershop_settings.EMBEDDING_MODEL,
            "llm_model": usershop_settings.GROQ_MODEL
        }
    except Exception as e:
        logger.error(f"[USERSHOP] Stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== SHOPGPT ENDPOINTS ====================
# Prefix: /api/shopping (matches frontend calls)

if SHOPGPT_AVAILABLE:
    # Include shopping router without prefix since it already has /api/shopping
    app.include_router(shopping.router, tags=["ShopGPT"])
    
    @app.get("/api/shopping/info")
    async def shopgpt_info():
        """ShopGPT: Get service information"""
        return {
            "message": "Smart Shopping Assistant API",
            "version": "3.0.0",
            "mode": "Real-time Shopping (Image-based)",
            "architecture": {
                "ai_models": {
                    "image_embedding": "SigLIP (Google)",
                    "ocr": "TrOCR (Microsoft)",
                    "captioning": "BLIP (Salesforce)",
                    "llm": "Groq (Llama 3.3 70B)"
                },
                "vector_db": "Qdrant Cloud",
                "storage": "SQLite + Qdrant"
            },
            "features": [
                "Image-based product search",
                "Real-time price comparison",
                "Multi-market support",
                "Virtual cart with budget tracking",
                "AI-powered recommendations",
                "Cheaper alternatives finder"
            ]
        }

# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    import uvicorn
    
    # Check for help argument
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print(__doc__)
        print("\nAvailable Services:")
        print("  • B2C Marketplace (/api/b2c/*)")
        if B2B_AVAILABLE:
            print("  • B2B Supplier Search (/api/b2b/*)")
        print("  • Usershop Recommendations (/api/usershop/*)")
        if SHOPGPT_AVAILABLE:
            print("  • ShopGPT Image Search (/api/shopping/*)")
        print("\nConfiguration:")
        print("  Host: 0.0.0.0")
        print("  Port: 8000")
        print("  Docs: http://localhost:8000/docs")
        print("\nTo modify configuration, edit the .env file")
        sys.exit(0)
    
    print("\n" + "=" * 80)
    print("🚀 STARTING UNIFIED MINERVA AI PLATFORM")
    print("=" * 80)
    print(f"📡 Server: http://0.0.0.0:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔧 Interactive API: http://localhost:8000/redoc")
    print("=" * 80)
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 80)
    print()
    
    try:
        uvicorn.run(
            "main_unified:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Unified Platform...")
        print("✅ Server stopped successfully")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
