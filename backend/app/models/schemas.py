from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ProductCategory(str, Enum):
    LAPTOP = "laptop"
    DESKTOP = "desktop"
    ACCESSORIES = "accessories"
    FOOD = "food"
    ELECTRONICS = "electronics"

class Market(str, Enum):
    TUNISIANET = "tunisianet"
    MYTEK = "mytek"
    AZIZA = "aziza"
    CARREFOUR = "carrefour"
    MG = "mg"
    GEANT = "geant"
    MONOPRIX = "monoprix"
    EL_MAZRAA = "el_mazraa"

class Product(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    market: str
    image_path: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None
    brand: Optional[str] = None

class SearchMode(str, Enum):
    PLANNING = "planning"
    SHOPPING = "shopping"

class PlanningSearchRequest(BaseModel):
    query: str = Field(..., description="User intent (e.g., 'Laptop for CS student')")
    budget: float = Field(..., gt=0, description="Maximum budget in TND")
    category: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)

class ShoppingSearchRequest(BaseModel):
    market: str = Field(..., description="Selected supermarket")
    budget: float = Field(..., gt=0, description="Total shopping budget in TND")
    category: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)

class CartItem(BaseModel):
    product: Product
    quantity: int = 1
    subtotal: float

class VirtualCart(BaseModel):
    items: List[CartItem] = []
    total: float = 0.0
    budget: float
    remaining: float
    is_over_budget: bool = False
    overspend_amount: float = 0.0

class Explanation(BaseModel):
    similarity_reason: str
    budget_status: str
    value_proposition: str
    alternatives_note: Optional[str] = None

class RecommendedProduct(BaseModel):
    product: Product
    similarity_score: float
    budget_compliance_score: float
    value_score: float
    final_score: float
    explanation: Explanation

class PlanningSearchResponse(BaseModel):
    query: str
    budget: float
    results: List[RecommendedProduct]
    total_found: int
    budget_exceeded_count: int
    message: Optional[str] = None

class ShoppingSearchResponse(BaseModel):
    market: str
    budget: float
    results: List[RecommendedProduct]
    cart: VirtualCart
    total_found: int
    message: Optional[str] = None

class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = 1

class CartResponse(BaseModel):
    cart: VirtualCart
    suggestions: Optional[List[Dict[str, Any]]] = None
    message: str
