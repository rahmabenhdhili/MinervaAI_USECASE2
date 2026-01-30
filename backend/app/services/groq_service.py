from openai import OpenAI
from typing import List, Dict, Any, Optional
from app.core.config import settings
import json

class GroqService:
    """
    Groq AI service for intelligent ranking and explanation generation.
    Uses Groq's ultra-fast inference for natural language recommendations.
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL
        )
        self.model = settings.GROQ_MODEL
    
    def rank_and_explain_products(
        self,
        query: str,
        budget: float,
        products: List[Dict[str, Any]],
        limit: int = 10,
        agent_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Use Groq AI to intelligently rank products and generate explanations.
        
        Integrates with agentic RAG system for enhanced reasoning.
        """
        
        # Prepare products data for Groq
        products_summary = []
        for i, product in enumerate(products[:20]):  # Limit to top 20 from vector search
            payload = product["payload"]
            products_summary.append({
                "index": i,
                "name": payload["name"],
                "price": payload["price"],
                "category": payload["category"],
                "market": payload["market"],
                "brand": payload.get("brand"),
                "description": payload["description"],
                "similarity_score": product["score"],
                "specs": payload.get("specs", {})
            })
        
        # Calculate budget metrics for context
        prices = [p["price"] for p in products_summary]
        avg_price = sum(prices) / len(prices) if prices else 0
        within_budget_count = sum(1 for p in prices if p <= budget)
        
        # Enhanced prompt with agent context
        agent_info = ""
        if agent_context:
            agent_info = f"\nAGENT ANALYSIS:\n{json.dumps(agent_context, indent=2)}\n"
        
        prompt = f"""You are a budget-aware shopping assistant for students in Tunisia. 

CONTEXT:
- User Query: "{query}"
- Budget: {budget} TND
- Products Found: {len(products_summary)}
- Within Budget: {within_budget_count}
- Average Price: {avg_price:.2f} TND
{agent_info}
PRODUCTS (with vector similarity scores):
{json.dumps(products_summary, indent=2)}

TASK:
Rank the top {limit} products considering:
1. Semantic relevance (similarity_score from vector search)
2. Budget constraints (prioritize within budget)
3. Value for money (price vs features)
4. Student needs (reliability, affordability)

For each product, provide:
- final_score (0-1): overall recommendation
- budget_compliance_score (0-1): budget fit
- value_score (0-1): value for money
- explanation:
  * similarity_reason: why it matches query
  * budget_status: budget relationship
  * value_proposition: why good value
  * alternatives_note: (if over budget) alternatives suggestion

Return ONLY valid JSON array:
[
  {{
    "product_index": 0,
    "final_score": 0.85,
    "budget_compliance_score": 0.90,
    "value_score": 0.80,
    "explanation": {{
      "similarity_reason": "...",
      "budget_status": "...",
      "value_proposition": "...",
      "alternatives_note": "..." or null
    }}
  }}
]

RULES:
- Prioritize within-budget products
- Be honest about over-budget items
- Consider student affordability
- Provide actionable explanations
- Use similarity scores as base relevance
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a budget-aware shopping assistant with agentic reasoning capabilities. Always return valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2500
            )
            
            # Parse Groq's response
            groq_response = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in groq_response:
                groq_response = groq_response.split("```json")[1].split("```")[0].strip()
            elif "```" in groq_response:
                groq_response = groq_response.split("```")[1].split("```")[0].strip()
            
            rankings = json.loads(groq_response)
            
            # Merge Groq rankings with original product data
            ranked_products = []
            for ranking in rankings:
                product_idx = ranking["product_index"]
                if product_idx < len(products):
                    product = products[product_idx]
                    ranked_products.append({
                        "product": product,
                        "final_score": ranking["final_score"],
                        "budget_compliance_score": ranking["budget_compliance_score"],
                        "value_score": ranking["value_score"],
                        "similarity_score": product["score"],
                        "explanation": ranking["explanation"]
                    })
            
            return ranked_products
        
        except Exception as e:
            print(f"Groq ranking error: {e}")
            # Fallback to simple ranking if Groq fails
            return self._fallback_ranking(products, budget, limit)
    
    def _fallback_ranking(
        self,
        products: List[Dict[str, Any]],
        budget: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback ranking if Groq fails"""
        ranked = []
        for product in products[:limit]:
            payload = product["payload"]
            price = payload["price"]
            similarity = product["score"]
            
            # Simple scoring
            budget_compliance = 1.0 if price <= budget else max(0.0, 1.0 - (price - budget) / budget)
            value_score = 1.0 - (price / budget) if price <= budget else 0.0
            final_score = similarity * 0.5 + budget_compliance * 0.3 + value_score * 0.2
            
            ranked.append({
                "product": product,
                "final_score": final_score,
                "budget_compliance_score": budget_compliance,
                "value_score": value_score,
                "similarity_score": similarity,
                "explanation": {
                    "similarity_reason": f"Matches your search with {similarity*100:.0f}% similarity",
                    "budget_status": f"Costs {price} TND vs budget {budget} TND",
                    "value_proposition": "Good value option" if price <= budget else "Above budget",
                    "alternatives_note": "Check other options" if price > budget else None
                }
            })
        
        return ranked

# Singleton instance
groq_service = GroqService()
