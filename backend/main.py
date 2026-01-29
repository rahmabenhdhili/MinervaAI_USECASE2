from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models import SearchQuery, RecommendationResponse
from services.recommendation_service import RecommendationService
from services.realtime_semantic_search_service import RealtimeSemanticSearchService
from services.marketing_service import MarketingService
from services.marketplace_service import MarketplaceService
from services.order_service import OrderService
from services.settings_service import SettingsService
from config import get_settings
from pydantic import BaseModel
from typing import Optional, List

# Service global
recommendation_service = None
realtime_search_service = None
marketing_service = None
marketplace_service = None
order_service = None
settings_service = None


class MarketingRequest(BaseModel):
    """Requête pour générer une stratégie marketing"""
    product_name: str
    product_description: str


class MarketingResponse(BaseModel):
    """Réponse avec la stratégie marketing"""
    product_name: str
    product_description: str
    strategy: str
    success: bool
    error: str = None


class MarketplaceProduct(BaseModel):
    """Produit de la marketplace"""
    name: str
    description: str
    price: float
    image_url: str
    category: str = "general"
    metadata: dict = {}


class MarketplaceProductUpdate(BaseModel):
    """Mise à jour d'un produit"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None


class OrderItem(BaseModel):
    """Item dans une commande"""
    product_id: str
    product_name: str
    product_image: str
    price: float
    quantity: int


class ShippingAddress(BaseModel):
    """Adresse de livraison"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str


class CreateOrderRequest(BaseModel):
    """Requête pour créer une commande (simplifiée)"""
    customer_name: str
    customer_phone: str
    shipping_address: dict
    items: List[dict]
    payment_method: str = "card"


class UpdateOrderStatusRequest(BaseModel):
    """Requête pour mettre à jour le statut"""
    status: str
    tracking_number: Optional[str] = None
    note: Optional[str] = None


class UpdateSettingsRequest(BaseModel):
    """Requête pour mettre à jour les paramètres de la marketplace"""
    marketplace_name: Optional[str] = None
    marketplace_logo: Optional[str] = None
    marketplace_description: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    global recommendation_service, realtime_search_service, marketing_service, marketplace_service, order_service, settings_service
    
    print("🚀 Initialisation de l'application...")
    recommendation_service = RecommendationService()
    await recommendation_service.initialize()
    
    # Service de recherche sémantique temps réel (Qdrant :memory: + FastEmbed)
    realtime_search_service = RealtimeSemanticSearchService()
    
    marketing_service = MarketingService(debug=True)
    marketplace_service = MarketplaceService(debug=True)
    order_service = OrderService(debug=True)
    settings_service = SettingsService(debug=True)
    
    print("✅ Application prête!")
    
    yield
    
    print("👋 Arrêt de l'application...")


# Configuration de l'application
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# CORS pour le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint de santé"""
    return {
        "status": "healthy",
        "service": "AI Product Recommendation System",
        "version": settings.api_version
    }


@app.get("/health")
async def health_check():
    """Vérification de santé détaillée"""
    return {
        "status": "healthy",
        "services": {
            "groq": "connected",
            "qdrant": "connected",
            "embedding": "loaded"
        }
    }


@app.post("/api/recommend", response_model=RecommendationResponse)
async def get_recommendations(query: SearchQuery):
    """
    Endpoint principal de recommandation
    
    Pipeline:
    1. Analyse de l'intention (Groq LLM)
    2. Collection de produits (Bright Data MCP)
    3. Génération d'embeddings (SentenceTransformers)
    4. Stockage vectoriel (Qdrant Cloud)
    5. Recherche sémantique (Cosine Similarity)
    6. Génération de recommandation (Groq LLM)
    """
    try:
        if not recommendation_service:
            raise HTTPException(
                status_code=503, 
                detail="Service not initialized"
            )
        
        result = await recommendation_service.get_recommendations(query)
        return result
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation error: {str(e)}"
        )


@app.post("/api/search/semantic")
async def semantic_search_realtime(query: SearchQuery):
    """
    🔍 RECHERCHE SÉMANTIQUE EN TEMPS RÉEL (AUDIT-COMPLIANT)
    
    ⚠️ ARCHITECTURE AUDIT:
    - Qdrant en mode :memory: (éphémère)
    - FastEmbed pour embeddings (Qdrant-compatible)
    - AUCUNE persistance des données scrapées
    - Collections temporaires supprimées après usage
    
    Pipeline:
    1. Scraping temps réel (pas de cache)
    2. Génération embeddings (FastEmbed)
    3. Création collection temporaire (Qdrant :memory:)
    4. Insertion temporaire dans Qdrant
    5. Recherche sémantique vectorielle
    6. Suppression collection (nettoyage)
    
    GARANTIES:
    - Données 100% temporaires (RAM uniquement)
    - Qdrant utilisé activement pour la recherche
    - Nettoyage explicite après chaque recherche
    """
    try:
        if not realtime_search_service:
            raise HTTPException(
                status_code=503,
                detail="Realtime search service not initialized"
            )
        
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
        print(f"❌ Erreur recherche sémantique: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search error: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """Statistiques du système"""
    try:
        # Récupérer les stats de Qdrant
        collection_info = recommendation_service.qdrant_service.client.get_collection(
            collection_name=settings.collection_name
        )
        
        return {
            "total_products": collection_info.points_count,
            "vector_dimension": settings.embedding_dimension,
            "collection_name": settings.collection_name
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_products": 0
        }


@app.post("/api/marketing", response_model=MarketingResponse)
async def generate_marketing_strategy(request: MarketingRequest):
    """
    Génère une stratégie marketing pour un produit
    
    Args:
        request: Nom et description du produit
    
    Returns:
        Stratégie marketing structurée
    """
    try:
        if not marketing_service:
            raise HTTPException(
                status_code=503,
                detail="Marketing service not initialized"
            )
        
        result = marketing_service.generate_marketing_strategy(
            product_name=request.product_name,
            product_description=request.product_description
        )
        
        return MarketingResponse(**result)
        
    except Exception as e:
        print(f"❌ Erreur marketing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Marketing strategy error: {str(e)}"
        )


# ==================== MARKETPLACE ENDPOINTS ====================

@app.post("/api/marketplace/products")
async def add_marketplace_product(product: MarketplaceProduct):
    """Ajoute un produit à la marketplace de l'utilisateur"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
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
        print(f"❌ Erreur ajout produit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding product: {str(e)}"
        )


@app.get("/api/marketplace/products")
async def get_marketplace_products():
    """Récupère tous les produits de la marketplace"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
        products = marketplace_service.get_all_products()
        return {
            "success": True,
            "products": products,
            "total": len(products)
        }
        
    except Exception as e:
        print(f"❌ Erreur récupération produits: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: {str(e)}"
        )


@app.get("/api/marketplace/products/{product_id}")
async def get_marketplace_product(product_id: str):
    """Récupère un produit spécifique"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
        product = marketplace_service.get_product(product_id)
        
        if product:
            return {
                "success": True,
                "product": product
            }
        else:
            raise HTTPException(status_code=404, detail="Product not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur récupération produit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching product: {str(e)}"
        )


@app.put("/api/marketplace/products/{product_id}")
async def update_marketplace_product(product_id: str, product: MarketplaceProductUpdate):
    """Met à jour un produit de la marketplace"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
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
        print(f"❌ Erreur mise à jour produit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating product: {str(e)}"
        )


@app.delete("/api/marketplace/products/{product_id}")
async def delete_marketplace_product(product_id: str):
    """Supprime un produit de la marketplace"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
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
        print(f"❌ Erreur suppression produit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting product: {str(e)}"
        )


@app.get("/api/marketplace/stats")
async def get_marketplace_stats():
    """Récupère les statistiques de la marketplace"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
        stats = marketplace_service.get_stats()
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ Erreur stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stats: {str(e)}"
        )


@app.post("/api/marketplace/products/{product_id}/click")
async def track_product_click(product_id: str):
    """Enregistre un clic sur un produit"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
        result = marketplace_service.increment_click(product_id)
        
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
        print(f"❌ Erreur tracking clic: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error tracking click: {str(e)}"
        )


@app.post("/api/marketplace/products/{product_id}/view")
async def track_product_view(product_id: str):
    """Enregistre une vue sur un produit"""
    try:
        if not marketplace_service:
            raise HTTPException(
                status_code=503,
                detail="Marketplace service not initialized"
            )
        
        result = marketplace_service.increment_view(product_id)
        
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
        print(f"❌ Erreur tracking vue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error tracking view: {str(e)}"
        )


# ==================== ORDER ENDPOINTS ====================

@app.post("/api/orders")
async def create_order(order_request: CreateOrderRequest):
    """Crée une nouvelle commande (automatiquement livrée)"""
    try:
        if not order_service:
            raise HTTPException(
                status_code=503,
                detail="Order service not initialized"
            )
        
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
        print(f"❌ Erreur création commande: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating order: {str(e)}"
        )


@app.get("/api/orders")
async def get_all_orders():
    """Récupère toutes les commandes"""
    try:
        if not order_service:
            raise HTTPException(
                status_code=503,
                detail="Order service not initialized"
            )
        
        orders = order_service.get_all_orders()
        return {
            "success": True,
            "orders": orders,
            "total": len(orders)
        }
        
    except Exception as e:
        print(f"❌ Erreur récupération commandes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching orders: {str(e)}"
        )


@app.get("/api/orders/delivered")
async def get_delivered_orders():
    """Récupère uniquement les commandes livrées"""
    try:
        if not order_service:
            raise HTTPException(
                status_code=503,
                detail="Order service not initialized"
            )
        
        orders = order_service.get_delivered_orders()
        return {
            "success": True,
            "orders": orders,
            "total": len(orders)
        }
        
    except Exception as e:
        print(f"❌ Erreur récupération commandes livrées: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching delivered orders: {str(e)}"
        )


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Récupère une commande spécifique"""
    try:
        if not order_service:
            raise HTTPException(
                status_code=503,
                detail="Order service not initialized"
            )
        
        order = order_service.get_order(order_id)
        
        if order:
            return {
                "success": True,
                "order": order
            }
        else:
            raise HTTPException(status_code=404, detail="Order not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur récupération commande: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching order: {str(e)}"
        )


@app.get("/api/orders/number/{order_number}")
async def get_order_by_number(order_number: str):
    """Récupère une commande par son numéro"""
    try:
        if not order_service:
            raise HTTPException(
                status_code=503,
                detail="Order service not initialized"
            )
        
        order = order_service.get_order_by_number(order_number)
        
        if order:
            return {
                "success": True,
                "order": order
            }
        else:
            raise HTTPException(status_code=404, detail="Order not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur récupération commande: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching order: {str(e)}"
        )


@app.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: str, status_request: UpdateOrderStatusRequest):
    """Met à jour le statut d'une commande"""
    try:
        if not order_service:
            raise HTTPException(
                status_code=503,
                detail="Order service not initialized"
            )
        
        result = order_service.update_order_status(
            order_id=order_id,
            status=status_request.status,
            tracking_number=status_request.tracking_number,
            note=status_request.note
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
        print(f"❌ Erreur mise à jour statut: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating status: {str(e)}"
        )


@app.get("/api/orders/stats")
async def get_order_stats():
    """Récupère les statistiques des commandes"""
    try:
        if not order_service:
            raise HTTPException(
                status_code=503,
                detail="Order service not initialized"
            )
        
        stats = order_service.get_stats()
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ Erreur stats commandes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stats: {str(e)}"
        )


# ==================== SETTINGS ENDPOINTS ====================

@app.get("/api/settings")
async def get_settings():
    """Récupère les paramètres de la marketplace"""
    try:
        if not settings_service:
            raise HTTPException(
                status_code=503,
                detail="Settings service not initialized"
            )
        
        settings = settings_service.get_settings()
        return {
            "success": True,
            "settings": settings
        }
        
    except Exception as e:
        print(f"❌ Erreur récupération settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching settings: {str(e)}"
        )


@app.put("/api/settings")
async def update_settings(settings_request: UpdateSettingsRequest):
    """Met à jour les paramètres de la marketplace"""
    try:
        if not settings_service:
            raise HTTPException(
                status_code=503,
                detail="Settings service not initialized"
            )
        
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
        print(f"❌ Erreur mise à jour settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating settings: {str(e)}"
        )


@app.post("/api/settings/reset")
async def reset_settings():
    """Réinitialise les paramètres aux valeurs par défaut"""
    try:
        if not settings_service:
            raise HTTPException(
                status_code=503,
                detail="Settings service not initialized"
            )
        
        result = settings_service.reset_settings()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur reset settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting settings: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)