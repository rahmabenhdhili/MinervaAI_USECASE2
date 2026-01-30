"""
Explainable AI Service for Budget-Aware Shopping
Provides transparent explanations for recommendations and budget warnings
"""
from typing import Dict, List, Optional, Tuple
from app.models.schemas import VirtualCart, CartItem, Product
from app.services.groq_service import groq_service
import json


class ExplainableAIService:
    """
    Provides explainable AI recommendations with clear reasoning
    """
    
    def analyze_budget_status(self, cart: VirtualCart) -> Dict:
        """
        Analyze cart budget status with detailed explanation
        
        Returns:
            - status: "safe", "warning", "over"
            - explanation: Clear explanation of the situation
            - percentage_used: How much of budget is used
            - recommendations: What to do next
        """
        percentage_used = (cart.total / cart.budget * 100) if cart.budget > 0 else 0
        remaining_percentage = 100 - percentage_used
        
        # Determine status
        if cart.total > cart.budget:
            status = "over"
            severity = "critical"
        elif percentage_used >= 95:
            status = "warning"
            severity = "high"
        elif percentage_used >= 85:
            status = "warning"
            severity = "medium"
        elif percentage_used >= 75:
            status = "warning"
            severity = "low"
        else:
            status = "safe"
            severity = "none"
        
        # Generate explanation
        explanation = self._generate_budget_explanation(
            cart, status, severity, percentage_used, remaining_percentage
        )
        
        # Generate recommendations
        recommendations = self._generate_budget_recommendations(
            cart, status, severity, percentage_used
        )
        
        return {
            "status": status,
            "severity": severity,
            "percentage_used": round(percentage_used, 1),
            "remaining_percentage": round(remaining_percentage, 1),
            "total": cart.total,
            "budget": cart.budget,
            "remaining": cart.remaining,
            "overspend": cart.overspend_amount,
            "explanation": explanation,
            "recommendations": recommendations,
            "item_count": len(cart.items),
            "average_item_price": round(cart.total / len(cart.items), 2) if cart.items else 0
        }
    
    def _generate_budget_explanation(
        self, 
        cart: VirtualCart, 
        status: str, 
        severity: str,
        percentage_used: float,
        remaining_percentage: float
    ) -> str:
        """Generate clear, human-readable budget explanation"""
        
        if status == "over":
            return (
                f"⚠️ **Budget Exceeded!** You're {cart.overspend_amount:.2f} TND over your budget. "
                f"Your cart total is {cart.total:.2f} TND but your budget is {cart.budget:.2f} TND. "
                f"You need to remove items or find cheaper alternatives to stay within budget."
            )
        
        elif status == "warning":
            if severity == "high":
                return (
                    f"⚠️ **Almost Over Budget!** You've used {percentage_used:.1f}% of your budget "
                    f"({cart.total:.2f} TND out of {cart.budget:.2f} TND). "
                    f"You only have {cart.remaining:.2f} TND left. Be very careful with additional items!"
                )
            elif severity == "medium":
                return (
                    f"⚡ **Approaching Budget Limit!** You've spent {percentage_used:.1f}% of your budget. "
                    f"You have {cart.remaining:.2f} TND remaining out of {cart.budget:.2f} TND. "
                    f"Consider if you really need more items."
                )
            else:  # low
                return (
                    f"💡 **Budget Alert:** You've used {percentage_used:.1f}% of your budget. "
                    f"You have {cart.remaining:.2f} TND left to spend. "
                    f"You're doing well, but keep an eye on your spending."
                )
        
        else:  # safe
            return (
                f"✅ **Within Budget:** You've used {percentage_used:.1f}% of your budget. "
                f"You have {cart.remaining:.2f} TND remaining out of {cart.budget:.2f} TND. "
                f"You're shopping responsibly!"
            )
    
    def _generate_budget_recommendations(
        self,
        cart: VirtualCart,
        status: str,
        severity: str,
        percentage_used: float
    ) -> List[str]:
        """Generate actionable recommendations based on budget status"""
        
        recommendations = []
        
        if status == "over":
            recommendations.extend([
                f"Remove items worth at least {cart.overspend_amount:.2f} TND",
                "Look for cheaper alternatives for expensive items",
                "Compare prices across different markets",
                "Consider reducing quantities of non-essential items"
            ])
        
        elif status == "warning":
            if severity == "high":
                recommendations.extend([
                    f"You can only add items worth up to {cart.remaining:.2f} TND",
                    "Avoid adding expensive items",
                    "Review your cart for non-essentials"
                ])
            elif severity == "medium":
                recommendations.extend([
                    f"You have {cart.remaining:.2f} TND left for additional items",
                    "Be selective with remaining purchases",
                    "Compare prices before adding more"
                ])
            else:  # low
                recommendations.extend([
                    f"You have {cart.remaining:.2f} TND remaining",
                    "You're on track, continue shopping wisely"
                ])
        
        else:  # safe
            recommendations.extend([
                f"You can still add items worth up to {cart.remaining:.2f} TND",
                "You're shopping within your means"
            ])
        
        return recommendations
    
    def explain_item_impact(
        self,
        cart: VirtualCart,
        product: Product,
        quantity: int = 1
    ) -> Dict:
        """
        Explain the impact of adding an item to the cart
        
        Returns detailed analysis of what happens if item is added
        """
        # Calculate new totals
        item_cost = product.price * quantity
        new_total = cart.total + item_cost
        new_remaining = cart.budget - new_total
        new_percentage = (new_total / cart.budget * 100) if cart.budget > 0 else 0
        
        # Determine if this would cause problems
        would_exceed = new_total > cart.budget
        would_warn = new_percentage >= 85
        
        # Generate explanation
        if would_exceed:
            overspend = new_total - cart.budget
            explanation = (
                f"❌ **Cannot Add:** Adding {quantity}x {product.name} ({item_cost:.2f} TND) "
                f"would put you {overspend:.2f} TND over budget. "
                f"Your total would be {new_total:.2f} TND, exceeding your {cart.budget:.2f} TND budget."
            )
            can_add = False
            suggestion = f"You need to remove {overspend:.2f} TND worth of items first, or find a cheaper alternative."
        
        elif would_warn:
            explanation = (
                f"⚠️ **Budget Warning:** Adding {quantity}x {product.name} ({item_cost:.2f} TND) "
                f"would use {new_percentage:.1f}% of your budget. "
                f"You'd only have {new_remaining:.2f} TND left."
            )
            can_add = True
            suggestion = "Consider if this item is essential before adding it."
        
        else:
            explanation = (
                f"✅ **Safe to Add:** Adding {quantity}x {product.name} ({item_cost:.2f} TND) "
                f"would use {new_percentage:.1f}% of your budget. "
                f"You'd still have {new_remaining:.2f} TND remaining."
            )
            can_add = True
            suggestion = "This item fits comfortably within your budget."
        
        return {
            "can_add": can_add,
            "would_exceed": would_exceed,
            "would_warn": would_warn,
            "item_cost": item_cost,
            "new_total": new_total,
            "new_remaining": new_remaining,
            "new_percentage": round(new_percentage, 1),
            "explanation": explanation,
            "suggestion": suggestion
        }
    
    async def get_smart_alternatives(
        self,
        cart: VirtualCart,
        all_products: List[Product],
        target_savings: float = None
    ) -> List[Dict]:
        """
        Get AI-powered alternatives with clear explanations
        
        Args:
            cart: Current cart
            all_products: Available products
            target_savings: How much to save (defaults to overspend amount)
        """
        if target_savings is None:
            target_savings = cart.overspend_amount if cart.is_over_budget else 0
        
        # Analyze cart items
        expensive_items = sorted(
            cart.items,
            key=lambda x: x.subtotal,
            reverse=True
        )
        
        suggestions = []
        
        # Strategy 1: Remove most expensive items
        if expensive_items:
            most_expensive = expensive_items[0]
            suggestions.append({
                "strategy": "remove",
                "item": most_expensive.product.name,
                "current_price": most_expensive.subtotal,
                "savings": most_expensive.subtotal,
                "explanation": (
                    f"Remove {most_expensive.product.name} ({most_expensive.subtotal:.2f} TND) - "
                    f"it's your most expensive item. This would save {most_expensive.subtotal:.2f} TND."
                ),
                "confidence": "high"
            })
        
        # Strategy 2: Find cheaper alternatives
        for cart_item in expensive_items[:3]:  # Top 3 expensive items
            # Find similar products that are cheaper
            similar_cheaper = [
                p for p in all_products
                if p.category == cart_item.product.category
                and p.price < cart_item.product.price
                and p.id != cart_item.product.id
            ]
            
            if similar_cheaper:
                cheapest = min(similar_cheaper, key=lambda x: x.price)
                savings = (cart_item.product.price - cheapest.price) * cart_item.quantity
                
                suggestions.append({
                    "strategy": "replace",
                    "item": cart_item.product.name,
                    "current_price": cart_item.product.price,
                    "alternative": cheapest.name,
                    "alternative_price": cheapest.price,
                    "alternative_market": cheapest.market,
                    "savings": savings,
                    "explanation": (
                        f"Replace {cart_item.product.name} ({cart_item.product.price:.2f} TND) "
                        f"with {cheapest.name} ({cheapest.price:.2f} TND) from {cheapest.market}. "
                        f"Save {savings:.2f} TND while getting a similar product."
                    ),
                    "confidence": "medium"
                })
        
        # Strategy 3: Reduce quantities
        for cart_item in expensive_items[:2]:
            if cart_item.quantity > 1:
                reduced_qty = cart_item.quantity - 1
                savings = cart_item.product.price
                
                suggestions.append({
                    "strategy": "reduce_quantity",
                    "item": cart_item.product.name,
                    "current_quantity": cart_item.quantity,
                    "suggested_quantity": reduced_qty,
                    "savings": savings,
                    "explanation": (
                        f"Reduce {cart_item.product.name} from {cart_item.quantity} to {reduced_qty}. "
                        f"Save {savings:.2f} TND. Do you really need that many?"
                    ),
                    "confidence": "medium"
                })
        
        # Sort by savings (highest first)
        suggestions.sort(key=lambda x: x["savings"], reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def generate_shopping_summary(self, cart: VirtualCart) -> Dict:
        """
        Generate a comprehensive shopping summary with insights
        """
        if not cart.items:
            return {
                "message": "Your cart is empty. Start adding items to see insights!",
                "insights": []
            }
        
        # Calculate insights
        most_expensive = max(cart.items, key=lambda x: x.subtotal)
        cheapest = min(cart.items, key=lambda x: x.subtotal)
        avg_price = cart.total / len(cart.items)
        
        # Group by market
        by_market = {}
        for item in cart.items:
            market = item.product.market
            if market not in by_market:
                by_market[market] = {"count": 0, "total": 0}
            by_market[market]["count"] += item.quantity
            by_market[market]["total"] += item.subtotal
        
        insights = [
            f"You have {len(cart.items)} different products in your cart",
            f"Average item price: {avg_price:.2f} TND",
            f"Most expensive item: {most_expensive.product.name} ({most_expensive.subtotal:.2f} TND)",
            f"Cheapest item: {cheapest.product.name} ({cheapest.subtotal:.2f} TND)"
        ]
        
        # Market distribution
        if len(by_market) > 1:
            insights.append(f"Shopping from {len(by_market)} different markets")
            for market, data in by_market.items():
                insights.append(f"  • {market}: {data['count']} items ({data['total']:.2f} TND)")
        
        return {
            "message": "Shopping Summary",
            "insights": insights,
            "by_market": by_market,
            "statistics": {
                "total_items": len(cart.items),
                "total_quantity": sum(item.quantity for item in cart.items),
                "average_price": round(avg_price, 2),
                "most_expensive": {
                    "name": most_expensive.product.name,
                    "price": most_expensive.subtotal
                },
                "cheapest": {
                    "name": cheapest.product.name,
                    "price": cheapest.subtotal
                }
            }
        }


# Singleton instance
explainable_ai_service = ExplainableAIService()
