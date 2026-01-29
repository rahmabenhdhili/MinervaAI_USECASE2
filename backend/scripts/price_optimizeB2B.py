from typing import List, Dict

class PriceOptimizer:
    def optimize(self, products: List[Dict], quantity: int, max_price: float = None, query: str = "") -> List[Dict]:
        optimized = []

        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 3]

        for product in products:
            try:
                product["unit_price"] = float(product.get("unit_price", 0))
                if product["unit_price"] <= 0:
                    continue
            except:
                continue

            product["quantity"] = quantity
            product["total_price"] = product["unit_price"] * quantity

            # Bonus for relevance
            name = product.get("product_name", "").lower()
            category = product.get("category", "").lower()
            bonus = 0.0
            for word in query_words:
                if word in name:
                    bonus += 0.2
                if word in category:
                    bonus += 0.1

            # Only include products that match at least one word
            if query_words and bonus == 0:
                continue

            # Convert similarity_score safely
            try:
                sim_score = float(product.get("similarity_score", 0))
            except (ValueError, TypeError):
                sim_score = 0.0

            product["adjusted_score"] = sim_score + bonus
            optimized.append(product)

        # Filter by max price after total_price is calculated
        if max_price is not None:
            optimized = [p for p in optimized if p["total_price"] <= max_price]

        # Sort by adjusted_score descending, then total_price ascending
        return sorted(
            optimized,
            key=lambda x: (-x.get("adjusted_score", 0), x.get("total_price", float("inf")))
        )
