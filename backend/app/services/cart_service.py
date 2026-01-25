from typing import Dict, List, Optional
from app.models.schemas import VirtualCart, CartItem, Product
from app.services.groq_service import groq_service
import json

class CartService:
    """
    Virtual cart service for Shopping Mode.
    Tracks items, calculates totals, detects overspending.
    """
    
    def __init__(self):
        # In-memory cart storage (use Redis/DB in production)
        self.carts: Dict[str, VirtualCart] = {}
    
    def create_cart(self, session_id: str, budget: float) -> VirtualCart:
        """Create a new virtual cart"""
        cart = VirtualCart(
            items=[],
            total=0.0,
            budget=budget,
            remaining=budget,
            is_over_budget=False,
            overspend_amount=0.0
        )
        self.carts[session_id] = cart
        return cart
    
    def get_cart(self, session_id: str) -> Optional[VirtualCart]:
        """Get existing cart"""
        return self.carts.get(session_id)
    
    def add_item(self, session_id: str, product: Product, quantity: int = 1, market: str = None) -> VirtualCart:
        """Add item to cart or increase quantity if already exists"""
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        # Check if item already in cart
        existing_item = next((item for item in cart.items if item.product.id == product.id), None)
        
        if existing_item:
            # Increase quantity
            existing_item.quantity += quantity
            existing_item.subtotal = existing_item.product.price * existing_item.quantity
        else:
            # Add new item
            cart_item = CartItem(
                product=product,
                quantity=quantity,
                subtotal=product.price * quantity
            )
            cart.items.append(cart_item)
        
        # Recalculate totals with tax
        self._recalculate_cart(cart, market)
        return cart
    
    def set_item_quantity(self, session_id: str, product_id: str, quantity: int, market: str = None) -> VirtualCart:
        """Set exact quantity for an item (replaces current quantity)"""
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            return self.remove_item(session_id, product_id, market)
        
        item = next((item for item in cart.items if item.product.id == product_id), None)
        if item:
            item.quantity = quantity
            item.subtotal = item.product.price * quantity
            self._recalculate_cart(cart, market)
        
        return cart
    
    def remove_item(self, session_id: str, product_id: str, market: str = None) -> VirtualCart:
        """Remove item completely from cart"""
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        cart.items = [item for item in cart.items if item.product.id != product_id]
        self._recalculate_cart(cart, market)
        return cart
    
    def decrease_quantity(self, session_id: str, product_id: str, amount: int = 1, market: str = None) -> VirtualCart:
        """Decrease item quantity by specified amount"""
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        item = next((item for item in cart.items if item.product.id == product_id), None)
        if item:
            item.quantity -= amount
            if item.quantity <= 0:
                # Remove item if quantity reaches 0
                return self.remove_item(session_id, product_id, market)
            item.subtotal = item.product.price * item.quantity
            self._recalculate_cart(cart, market)
        
        return cart
    
    def update_quantity(self, session_id: str, product_id: str, quantity: int, market: str = None) -> VirtualCart:
        """Update item quantity (alias for set_item_quantity)"""
        return self.set_item_quantity(session_id, product_id, quantity, market)
    
    def clear_cart(self, session_id: str) -> VirtualCart:
        """Clear all items from cart"""
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        cart.items = []
        self._recalculate_cart(cart)
        return cart
    
    def _recalculate_cart(self, cart: VirtualCart, market: str = None):
        """Recalculate cart totals with tax"""
        subtotal = sum(item.subtotal for item in cart.items)
        
        # Apply tax based on market
        # Aziza: 100 millimes (0.1 TND) flat fee per shopping session (not per item)
        tax = 0.0
        if market and market.lower() == 'aziza' and len(cart.items) > 0:
            tax = 0.1  # Flat 100 millimes fee for the entire cart
        
        cart.total = subtotal + tax
        cart.remaining = cart.budget - cart.total
        cart.is_over_budget = cart.total > cart.budget
        cart.overspend_amount = max(0, cart.total - cart.budget)
    
    async def get_suggestions(self, cart: VirtualCart, all_products: List[Product]) -> List[Dict]:
        """
        Get Groq AI suggestions for cart optimization.
        - Remove expensive items
        - Suggest cheaper alternatives
        - Find same product in cheaper market
        """
        if not cart.is_over_budget:
            return []
        
        # Prepare cart summary for Groq
        cart_summary = {
            "total": cart.total,
            "budget": cart.budget,
            "overspend": cart.overspend_amount,
            "items": [
                {
                    "name": item.product.name,
                    "price": item.product.price,
                    "quantity": item.quantity,
                    "subtotal": item.subtotal,
                    "market": item.product.market
                }
                for item in cart.items
            ]
        }
        
        # Get available alternatives
        alternatives_summary = [
            {
                "name": p.name,
                "price": p.price,
                "market": p.market,
                "category": p.category
            }
            for p in all_products[:20]  # Limit for Groq
        ]
        
        prompt = f"""You are a budget-aware shopping assistant. The user's cart is over budget.

Cart Summary:
{json.dumps(cart_summary, indent=2)}

Available Alternatives:
{json.dumps(alternatives_summary, indent=2)}

Task: Provide 3 actionable suggestions to bring the cart within budget:
1. Remove the most expensive non-essential item
2. Replace an item with a cheaper alternative
3. Find the same product in a cheaper market

Return ONLY valid JSON array:
[
  {{
    "action": "remove" | "replace" | "switch_market",
    "item_name": "...",
    "reason": "...",
    "savings": 0.0,
    "alternative": "..." (if replace/switch)
  }}
]
"""

        try:
            from openai import OpenAI
            from app.core.config import settings
            
            client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url=settings.GROQ_BASE_URL
            )
            
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a budget optimization assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in suggestions_text:
                suggestions_text = suggestions_text.split("```json")[1].split("```")[0].strip()
            elif "```" in suggestions_text:
                suggestions_text = suggestions_text.split("```")[1].split("```")[0].strip()
            
            suggestions = json.loads(suggestions_text)
            return suggestions
        
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []

# Singleton instance
cart_service = CartService()
