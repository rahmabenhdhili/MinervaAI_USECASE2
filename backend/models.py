from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Product(BaseModel):
    """Modèle de produit"""
    id: str
    name: str
    description: str
    price: float
    url: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchQuery(BaseModel):
    """Requête de recherche utilisateur"""
    query: str = Field(..., min_length=3, description="Requête en langage naturel")
    max_results: int = Field(default=20, ge=1, le=30, description="Nombre de résultats")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filtres optionnels")
    use_amazon: bool = Field(default=True, description="Utiliser Amazon")
    use_alibaba: bool = Field(default=True, description="Utiliser Alibaba")
    use_walmart: bool = Field(default=False, description="Utiliser Walmart (Firecrawl)")
    use_cdiscount: bool = Field(default=False, description="Utiliser Cdiscount (Firecrawl)")


class QueryIntent(BaseModel):
    """Intention extraite de la requête"""
    product_type: str
    usage: Optional[str] = None
    budget_range: Optional[str] = None
    key_features: List[str] = []
    search_keywords: List[str] = []


class ProductRecommendation(BaseModel):
    """Produit avec score de similarité"""
    product: Product
    similarity_score: float = Field(..., ge=-1.0, le=1.0)  # Cosine peut être négatif
    relevance_explanation: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Réponse complète du système"""
    query: str
    intent: QueryIntent
    recommendations: List[ProductRecommendation]
    summary: str
    total_found: int
