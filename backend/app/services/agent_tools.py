"""
Agentic RAG Tools - Lightweight tool-based architecture for intelligent shopping assistance.

This module provides a set of tools that an agent can use for multi-step reasoning:
- Database queries (product search, filtering)
- Calculator (budget calculations, price comparisons)
- Price analysis (find best deals, alternatives)
- Reasoning (multi-step decision making)
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import json
from app.services.qdrant_service import qdrant_service
from app.services.hybrid_search_service import hybrid_search_service
from app.core.config import settings
import sys
from pathlib import Path

# Add data_pipeline to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from data_pipeline.product_database import product_db


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any
    reasoning: str
    next_steps: Optional[List[str]] = None


class AgentTool:
    """Base class for agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        raise NotImplementedError


class DatabaseQueryTool(AgentTool):
    """Tool for querying product database"""
    
    def __init__(self):
        super().__init__(
            name="database_query",
            description="Search and filter products from database using vector similarity and filters"
        )
    
    def execute(
        self,
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        market: Optional[str] = None,
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> ToolResult:
        """
        Query products with multiple search strategies
        
        Args:
            query_vector: Image embedding for visual search
            query_text: Text query for hybrid search
            market: Filter by specific market
            max_price: Maximum price filter
            category: Product category filter
            limit: Number of results
        """
        try:
            results = []
            reasoning = []
            
            # Strategy 1: Hybrid search (image + text)
            if query_vector and query_text:
                reasoning.append(f"Using hybrid search (visual + text: '{query_text}')")
                results = hybrid_search_service.hybrid_search(
                    image_embedding=query_vector,
                    query_text=query_text,
                    collection_name=settings.COLLECTION_SUPERMARKET,
                    market=market,
                    limit=limit
                )
            
            # Strategy 2: Pure visual search
            elif query_vector:
                reasoning.append("Using pure visual search")
                results = qdrant_service.search_products(
                    collection_name=settings.COLLECTION_SUPERMARKET,
                    query_vector=query_vector,
                    max_price=max_price,
                    category=category,
                    limit=limit,
                    use_mmr=False
                )
                
                # Filter by market if specified
                if market:
                    results = [r for r in results if r["payload"]["market"] == market]
            
            # Strategy 3: Fallback to SQLite
            else:
                reasoning.append("Fallback to SQLite database")
                db_products = product_db.get_products_by_market(market, limit=limit) if market else []
                results = [{"payload": p, "score": 0.5} for p in db_products]
            
            # Apply additional filters
            if max_price:
                results = [r for r in results if r["payload"]["price"] <= max_price]
                reasoning.append(f"Filtered by max price: {max_price} TND")
            
            if category:
                results = [r for r in results if r["payload"].get("category") == category]
                reasoning.append(f"Filtered by category: {category}")
            
            next_steps = []
            if len(results) == 0:
                next_steps.append("Try broader search criteria")
                next_steps.append("Check other markets")
            elif len(results) > 5:
                next_steps.append("Use calculator to analyze prices")
                next_steps.append("Find cheaper alternatives")
            
            return ToolResult(
                success=True,
                data=results,
                reasoning=" | ".join(reasoning),
                next_steps=next_steps
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                reasoning=f"Database query failed: {str(e)}",
                next_steps=["Retry with different parameters"]
            )


class CalculatorTool(AgentTool):
    """Tool for budget and price calculations"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform budget calculations, price analysis, and financial reasoning"
        )
    
    def execute(
        self,
        operation: str,
        products: Optional[List[Dict]] = None,
        budget: Optional[float] = None,
        **kwargs
    ) -> ToolResult:
        """
        Perform calculations
        
        Operations:
        - budget_analysis: Analyze products against budget
        - quantity_suggestion: Suggest optimal quantity
        - savings_calculation: Calculate potential savings
        - affordability_check: Check if products are affordable
        """
        try:
            if operation == "budget_analysis":
                return self._budget_analysis(products, budget)
            elif operation == "quantity_suggestion":
                return self._quantity_suggestion(products[0] if products else None, budget)
            elif operation == "savings_calculation":
                return self._savings_calculation(products, kwargs.get("current_price"))
            elif operation == "affordability_check":
                return self._affordability_check(products, budget)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    reasoning=f"Unknown operation: {operation}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                reasoning=f"Calculator error: {str(e)}"
            )
    
    def _budget_analysis(self, products: List[Dict], budget: float) -> ToolResult:
        """Analyze products against budget"""
        if not products:
            return ToolResult(success=False, data=None, reasoning="No products to analyze")
        
        prices = [p.get("payload", p).get("price", 0) for p in products]
        within_budget = [p for p in prices if p <= budget]
        over_budget = [p for p in prices if p > budget]
        
        analysis = {
            "total_products": len(products),
            "within_budget_count": len(within_budget),
            "over_budget_count": len(over_budget),
            "cheapest": min(prices) if prices else 0,
            "most_expensive": max(prices) if prices else 0,
            "average": sum(prices) / len(prices) if prices else 0,
            "budget": budget,
            "budget_utilization": {
                "cheapest_pct": (min(prices) / budget * 100) if prices and budget > 0 else 0,
                "average_pct": (sum(prices) / len(prices) / budget * 100) if prices and budget > 0 else 0
            }
        }
        
        reasoning = f"Found {len(within_budget)} products within budget ({len(over_budget)} over budget). "
        reasoning += f"Price range: {analysis['cheapest']:.2f} - {analysis['most_expensive']:.2f} TND"
        
        next_steps = []
        if len(within_budget) > 0:
            next_steps.append("Recommend cheapest within-budget option")
        if len(over_budget) > 0:
            next_steps.append("Find cheaper alternatives in other markets")
        
        return ToolResult(
            success=True,
            data=analysis,
            reasoning=reasoning,
            next_steps=next_steps
        )
    
    def _quantity_suggestion(self, product: Dict, budget: float) -> ToolResult:
        """Suggest optimal quantity based on budget"""
        if not product:
            return ToolResult(success=False, data=None, reasoning="No product provided")
        
        price = product.get("payload", product).get("price", 0)
        
        if price <= 0:
            return ToolResult(success=False, data=None, reasoning="Invalid price")
        
        max_affordable = int(budget / price)
        
        # Smart quantity logic
        if price < budget * 0.3:  # Less than 30% of budget
            if max_affordable >= 6:
                suggested = 6
                reasoning = "6-pack (bulk savings)"
            elif max_affordable >= 4:
                suggested = 4
                reasoning = "4-pack (family size)"
            elif max_affordable >= 2:
                suggested = 2
                reasoning = "2-pack (stock up)"
            else:
                suggested = 1
                reasoning = "single unit"
        elif price <= budget:
            suggested = 1
            reasoning = "single unit (fits budget)"
        else:
            suggested = 1
            reasoning = "over budget - consider alternatives"
        
        total = price * suggested
        
        return ToolResult(
            success=True,
            data={
                "quantity": suggested,
                "reasoning": reasoning,
                "unit_price": price,
                "total_price": total,
                "within_budget": total <= budget,
                "max_affordable": max_affordable
            },
            reasoning=f"Suggest {suggested} units ({reasoning}) for {total:.2f} TND",
            next_steps=["Add to cart" if total <= budget else "Find cheaper alternative"]
        )
    
    def _savings_calculation(self, alternatives: List[Dict], current_price: float) -> ToolResult:
        """Calculate savings from alternatives"""
        if not alternatives:
            return ToolResult(
                success=True,
                data={"savings": 0, "alternatives": []},
                reasoning="No cheaper alternatives found"
            )
        
        savings_list = []
        for alt in alternatives:
            alt_price = alt.get("payload", alt).get("price", 0)
            if alt_price < current_price:
                savings = current_price - alt_price
                percentage = (savings / current_price) * 100
                savings_list.append({
                    "product": alt,
                    "savings": savings,
                    "percentage": percentage
                })
        
        savings_list.sort(key=lambda x: x["savings"], reverse=True)
        
        if savings_list:
            best = savings_list[0]
            reasoning = f"Best alternative saves {best['savings']:.2f} TND ({best['percentage']:.1f}% cheaper)"
        else:
            reasoning = "Current option is the cheapest"
        
        return ToolResult(
            success=True,
            data={"alternatives": savings_list},
            reasoning=reasoning,
            next_steps=["Recommend best alternative"] if savings_list else []
        )
    
    def _affordability_check(self, products: List[Dict], budget: float) -> ToolResult:
        """Check which products are affordable"""
        affordable = []
        unaffordable = []
        
        for product in products:
            price = product.get("payload", product).get("price", 0)
            if price <= budget:
                affordable.append(product)
            else:
                unaffordable.append(product)
        
        return ToolResult(
            success=True,
            data={
                "affordable": affordable,
                "unaffordable": unaffordable,
                "affordable_count": len(affordable)
            },
            reasoning=f"{len(affordable)} products within budget, {len(unaffordable)} over budget",
            next_steps=["Rank affordable products by value"] if affordable else ["Search other markets"]
        )


class PriceAnalysisTool(AgentTool):
    """Tool for price comparison and deal finding"""
    
    def __init__(self):
        super().__init__(
            name="price_analysis",
            description="Find best deals, compare prices across markets, identify savings opportunities"
        )
    
    def execute(
        self,
        operation: str,
        product: Optional[Dict] = None,
        all_results: Optional[List[Dict]] = None,
        current_market: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Perform price analysis
        
        Operations:
        - find_alternatives: Find cheaper alternatives in other markets
        - best_deal: Find absolute best deal
        - market_comparison: Compare prices across all markets
        """
        try:
            if operation == "find_alternatives":
                return self._find_alternatives(product, all_results, current_market)
            elif operation == "best_deal":
                return self._find_best_deal(all_results)
            elif operation == "market_comparison":
                return self._market_comparison(all_results)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    reasoning=f"Unknown operation: {operation}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                reasoning=f"Price analysis error: {str(e)}"
            )
    
    def _find_alternatives(
        self,
        product: Dict,
        all_results: List[Dict],
        current_market: str
    ) -> ToolResult:
        """Find cheaper alternatives in other markets"""
        if not product or not all_results:
            return ToolResult(success=False, data=None, reasoning="Missing data")
        
        current_price = product.get("payload", product).get("price", 0)
        
        # Find similar products from other markets that are cheaper
        alternatives = []
        for result in all_results:
            payload = result.get("payload", result)
            if (payload.get("market") != current_market and
                payload.get("price", 0) < current_price and
                result.get("score", 0) > 0.7):  # High similarity
                
                savings = current_price - payload["price"]
                percentage = (savings / current_price) * 100
                
                alternatives.append({
                    "product": result,
                    "savings": savings,
                    "percentage": percentage,
                    "similarity": result.get("score", 0)
                })
        
        alternatives.sort(key=lambda x: x["savings"], reverse=True)
        
        if alternatives:
            reasoning = f"Found {len(alternatives)} cheaper alternatives. "
            reasoning += f"Best saves {alternatives[0]['savings']:.2f} TND ({alternatives[0]['percentage']:.1f}%)"
        else:
            reasoning = f"{current_market} has the best price"
        
        return ToolResult(
            success=True,
            data=alternatives[:3],  # Top 3
            reasoning=reasoning,
            next_steps=["Present alternatives to user"] if alternatives else []
        )
    
    def _find_best_deal(self, all_results: List[Dict]) -> ToolResult:
        """Find the absolute best deal"""
        if not all_results:
            return ToolResult(success=False, data=None, reasoning="No results")
        
        # Sort by price (cheapest first)
        sorted_results = sorted(
            all_results,
            key=lambda x: x.get("payload", x).get("price", float('inf'))
        )
        
        best = sorted_results[0]
        payload = best.get("payload", best)
        
        return ToolResult(
            success=True,
            data=best,
            reasoning=f"Best deal: {payload['name']} at {payload['market']} for {payload['price']} TND",
            next_steps=["Recommend to user"]
        )
    
    def _market_comparison(self, all_results: List[Dict]) -> ToolResult:
        """Compare prices across markets"""
        if not all_results:
            return ToolResult(success=False, data=None, reasoning="No results")
        
        by_market = {}
        for result in all_results:
            payload = result.get("payload", result)
            market = payload.get("market")
            price = payload.get("price", 0)
            
            if market not in by_market:
                by_market[market] = []
            by_market[market].append(price)
        
        comparison = {}
        for market, prices in by_market.items():
            comparison[market] = {
                "count": len(prices),
                "avg_price": sum(prices) / len(prices),
                "min_price": min(prices),
                "max_price": max(prices)
            }
        
        # Find cheapest market
        cheapest_market = min(comparison.items(), key=lambda x: x[1]["avg_price"])
        
        return ToolResult(
            success=True,
            data=comparison,
            reasoning=f"Cheapest market: {cheapest_market[0]} (avg: {cheapest_market[1]['avg_price']:.2f} TND)",
            next_steps=["Recommend cheapest market"]
        )


class AgentOrchestrator:
    """
    Lightweight agentic orchestrator with multi-step reasoning and feedback loops.
    
    This orchestrator:
    1. Executes tools in sequence based on context
    2. Uses feedback from one tool to inform the next
    3. Makes intelligent decisions about which tools to use
    4. Provides reasoning for all actions
    """
    
    def __init__(self):
        self.tools = {
            "database": DatabaseQueryTool(),
            "calculator": CalculatorTool(),
            "price_analysis": PriceAnalysisTool()
        }
        self.execution_log = []
    
    def execute_workflow(
        self,
        query_vector: Optional[List[float]],
        query_text: Optional[str],
        market: str,
        budget: float,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Execute a multi-step agentic workflow for product search
        
        Workflow:
        1. Query database (visual + text search)
        2. Analyze budget (calculator)
        3. Find alternatives (price analysis)
        4. Make recommendation (reasoning)
        """
        self.execution_log = []
        
        # Step 1: Database Query
        print("🤖 Agent Step 1: Querying database...")
        db_result = self.tools["database"].execute(
            query_vector=query_vector,
            query_text=query_text,
            market=market,
            limit=limit
        )
        self.execution_log.append({"step": 1, "tool": "database", "result": db_result})
        
        if not db_result.success or not db_result.data:
            return {
                "success": False,
                "message": "No products found",
                "reasoning": db_result.reasoning,
                "execution_log": self.execution_log
            }
        
        market_results = db_result.data
        print(f"   ✓ Found {len(market_results)} products")
        
        # Also search all markets for price comparison
        all_markets_result = self.tools["database"].execute(
            query_vector=query_vector,
            query_text=query_text,
            market=None,  # All markets
            limit=20
        )
        all_results = all_markets_result.data if all_markets_result.success else []
        
        # Step 2: Budget Analysis
        print("🤖 Agent Step 2: Analyzing budget...")
        budget_result = self.tools["calculator"].execute(
            operation="budget_analysis",
            products=market_results,
            budget=budget
        )
        self.execution_log.append({"step": 2, "tool": "calculator", "result": budget_result})
        print(f"   ✓ {budget_result.reasoning}")
        
        # Step 3: Get best match
        best_match = market_results[0]
        best_product = best_match.get("payload", best_match)
        
        # Step 4: Quantity Suggestion
        print("🤖 Agent Step 3: Calculating optimal quantity...")
        quantity_result = self.tools["calculator"].execute(
            operation="quantity_suggestion",
            products=[best_match],
            budget=budget
        )
        self.execution_log.append({"step": 3, "tool": "calculator", "result": quantity_result})
        print(f"   ✓ {quantity_result.reasoning}")
        
        # Step 5: Find Alternatives
        print("🤖 Agent Step 4: Finding cheaper alternatives...")
        alternatives_result = self.tools["price_analysis"].execute(
            operation="find_alternatives",
            product=best_match,
            all_results=all_results,
            current_market=market
        )
        self.execution_log.append({"step": 4, "tool": "price_analysis", "result": alternatives_result})
        print(f"   ✓ {alternatives_result.reasoning}")
        
        # Step 6: Make Final Recommendation
        within_budget = best_product["price"] <= budget
        
        recommendation = self._generate_recommendation(
            best_match=best_match,
            budget=budget,
            quantity_data=quantity_result.data if quantity_result.success else None,
            alternatives=alternatives_result.data if alternatives_result.success else [],
            within_budget=within_budget
        )
        
        return {
            "success": True,
            "best_match": best_match,
            "quantity_suggestion": quantity_result.data if quantity_result.success else None,
            "alternatives": alternatives_result.data if alternatives_result.success else [],
            "budget_analysis": budget_result.data if budget_result.success else None,
            "recommendation": recommendation,
            "reasoning_chain": [log["result"].reasoning for log in self.execution_log],
            "execution_log": self.execution_log
        }
    
    def _generate_recommendation(
        self,
        best_match: Dict,
        budget: float,
        quantity_data: Optional[Dict],
        alternatives: List[Dict],
        within_budget: bool
    ) -> str:
        """Generate final recommendation based on all analysis"""
        product = best_match.get("payload", best_match)
        
        rec = []
        
        # Product info
        if quantity_data:
            qty = quantity_data["quantity"]
            total = quantity_data["total_price"]
            rec.append(f"Get {qty}x {product['name']} for {total:.2f} TND ({quantity_data['reasoning']})")
        else:
            rec.append(f"Found: {product['name']} at {product['price']} TND")
        
        # Budget status
        if within_budget:
            rec.append("✓ Within your budget")
        else:
            over = product['price'] - budget
            rec.append(f"⚠️ Over budget by {over:.2f} TND")
        
        # Alternatives
        if alternatives:
            best_alt = alternatives[0]
            alt_product = best_alt["product"].get("payload", best_alt["product"])
            rec.append(f"💡 Cheaper at {alt_product['market']}: {alt_product['price']} TND (save {best_alt['savings']:.2f} TND)")
        else:
            rec.append(f"✓ Best price available")
        
        return " | ".join(rec)


# Singleton instance
agent_orchestrator = AgentOrchestrator()
