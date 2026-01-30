from typing import Dict, List, Optional
from app.models.schemas import VirtualCart, CartItem, Product
from app.services.groq_service import groq_service
from app.services.explainable_ai_service import explainable_ai_service
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
    
    def add_item(self, session_id: str, product: Product, quantity: int = 1, market: str = None) -> Dict:
        """Add item to cart or increase quantity if already exists
        
        Returns cart with budget analysis and explanations
        """
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        # Analyze impact before adding
        impact_analysis = explainable_ai_service.explain_item_impact(cart, product, quantity)
        
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
        
        # Get budget analysis
        budget_status = explainable_ai_service.analyze_budget_status(cart)
        
        return {
            "cart": cart,
            "budget_status": budget_status,
            "item_added": {
                "name": product.name,
                "quantity": quantity,
                "price": product.price,
                "subtotal": product.price * quantity
            },
            "impact_analysis": impact_analysis
        }
    
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
        
        # Apply 0.1 TND "Droit de timbre" for all markets when cart has items
        tax = 0.1 if len(cart.items) > 0 else 0.0
        
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
        
        # Use explainable AI service for better suggestions
        return await explainable_ai_service.get_smart_alternatives(cart, all_products)
    
    def get_cart_analysis(self, session_id: str) -> Dict:
        """
        Get comprehensive cart analysis with explainable AI insights
        """
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        # Get budget status
        budget_status = explainable_ai_service.analyze_budget_status(cart)
        
        # Get shopping summary
        shopping_summary = explainable_ai_service.generate_shopping_summary(cart)
        
        return {
            "cart": cart,
            "budget_status": budget_status,
            "shopping_summary": shopping_summary
        }
    
    async def get_optimization_suggestions(
        self, 
        session_id: str, 
        all_products: List[Product]
    ) -> Dict:
        """
        Get AI-powered optimization suggestions with explanations
        """
        cart = self.get_cart(session_id)
        if not cart:
            raise ValueError("Cart not found")
        
        # Get budget analysis
        budget_status = explainable_ai_service.analyze_budget_status(cart)
        
        # Get smart alternatives
        alternatives = await explainable_ai_service.get_smart_alternatives(
            cart, 
            all_products,
            target_savings=cart.overspend_amount if cart.is_over_budget else None
        )
        
        return {
            "budget_status": budget_status,
            "alternatives": alternatives,
            "needs_optimization": cart.is_over_budget or budget_status["percentage_used"] >= 85
        }

# Singleton instance
cart_service = CartService()
