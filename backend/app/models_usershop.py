from pydantic import BaseModel
from typing import List, Optional

class Product(BaseModel):
    id: Optional[str] = None
    url: str
    name: str
    category: str
    brand: str
    img: str
    description: str
    price: str

class ProductRecommendation(BaseModel):
    id: Optional[str] = None  # ID du produit dans Qdrant
    name: str
    category: str
    brand: str
    price: str
    img: str
    url: str
    score: Optional[float] = None  # Score de pertinence
    price_numeric: Optional[float] = None  # Prix numérique pour tri

class RecommendationRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None  # Prix minimum
    max_price: Optional[float] = None  # Prix maximum
    sort_by: Optional[str] = "relevance"  # relevance, price_asc, price_desc
    limit: Optional[int] = None  # Nombre de résultats (None = tous)

class RecommendationResponse(BaseModel):
    product_description: str
    recommendations: List[ProductRecommendation]

class ProductSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

class ProductComparisonRequest(BaseModel):
    product_id_1: str
    product_id_2: str

class MonetaryGuide(BaseModel):
    price_difference: str
    value_analysis: str
    budget_recommendation: str
    long_term_cost: str

class TechnicalGuide(BaseModel):
    quality_comparison: str
    features_comparison: str
    durability_analysis: str
    performance_rating: str

class ProductAnalysis(BaseModel):
    product_name: str
    price: str
    explanation: str
    advantages: List[str]
    disadvantages: List[str]
    best_for: str

class ComparisonResponse(BaseModel):
    product_1_analysis: ProductAnalysis
    product_2_analysis: ProductAnalysis
    monetary_guide: MonetaryGuide
    technical_guide: TechnicalGuide
    final_recommendation: str
    recommendation_reason: str