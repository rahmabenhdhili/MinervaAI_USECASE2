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
    name: str
    category: str
    brand: str
    price: str
    img: str
    url: str

class RecommendationRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None  # Prix minimum
    max_price: Optional[float] = None  # Prix maximum

class RecommendationResponse(BaseModel):
    product_description: str
    recommendations: List[ProductRecommendation]

class ProductSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5