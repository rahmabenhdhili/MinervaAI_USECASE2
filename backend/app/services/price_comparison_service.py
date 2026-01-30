"""
Price comparison service for cross-market product search.
Finds the same product across different supermarkets and suggests the cheapest option.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

# Add data_pipeline to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from data_pipeline.product_database import product_db

class PriceComparisonService:
    """
    Compare prices across supermarkets.
    Find the same product in different markets and suggest the cheapest.
    """
    
    def __init__(self):
        self.similarity_threshold = 0.7  # 70% name similarity
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two product names"""
        # Normalize names
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, name1, name2).ratio()
    
    def _normalize_product_name(self, name: str) -> str:
        """
        Normalize product name for better matching.
        Extracts core product name by removing sizes, quantities, and extra details.
        
        Example:
        "YAB Yaourt aromatisé à la banane 100 G" → "yab yaourt aromatisé banane"
        """
        name = name.lower()
        
        # Remove size/quantity patterns
        import re
        
        # Remove weight/volume: 100 G, 1L, 500ml, 1.5kg, etc.
        name = re.sub(r'\d+[.,]?\d*\s*(g|kg|ml|l|cl|dl)\b', '', name, flags=re.IGNORECASE)
        
        # Remove pack quantities: pack de 6, lot de 2, x2, etc.
        name = re.sub(r'(pack|lot|x)\s*(de\s*)?\d+', '', name, flags=re.IGNORECASE)
        
        # Remove common filler words
        filler_words = ['à', 'la', 'le', 'de', 'du', 'des', 'au', 'aux']
        words = name.split()
        words = [w for w in words if w not in filler_words or len(w) > 2]
        
        # Remove extra spaces
        name = ' '.join(words)
        
        return name.strip()
    
    def find_same_product_in_other_markets(
        self,
        product_name: str,
        current_market: str,
        current_price: float,
        brand: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find the same product in other supermarkets.
        Uses brand + core name for better matching.
        Returns list of alternatives with price comparison.
        """
        # Normalize the search name
        normalized_search = self._normalize_product_name(product_name)
        
        # Extract brand from name if not provided
        if not brand:
            # Try to extract brand (usually first word)
            words = product_name.split()
            if words:
                brand = words[0].upper()
        
        # Get all products from database
        all_products = product_db.get_all_products(limit=5000)
        
        # Find similar products in other markets
        alternatives = []
        
        for db_product in all_products:
            # Skip same market
            if db_product['market'] == current_market:
                continue
            
            # Calculate name similarity
            normalized_db_name = self._normalize_product_name(db_product['name'])
            name_similarity = self._calculate_name_similarity(normalized_search, normalized_db_name)
            
            # Boost similarity if brands match
            db_brand = db_product.get('brand')
            brand_match = False
            if brand and db_brand:
                # Both brands exist, check if they match
                if brand.upper() in db_brand.upper():
                    name_similarity = min(1.0, name_similarity + 0.2)  # Boost by 20%
                    brand_match = True
            
            # If similar enough, add as alternative
            if name_similarity >= self.similarity_threshold:
                price_diff = db_product['price'] - current_price
                savings = -price_diff if price_diff < 0 else 0
                
                alternatives.append({
                    'product_id': db_product['product_id'],
                    'name': db_product['name'],
                    'market': db_product['market'],
                    'price': db_product['price'],
                    'brand': db_product.get('brand'),
                    'similarity': name_similarity,
                    'brand_match': brand_match,
                    'price_difference': price_diff,
                    'savings': savings,
                    'is_cheaper': price_diff < 0,
                    'percentage_cheaper': (savings / current_price * 100) if savings > 0 else 0
                })
        
        # Sort by: 1) brand match, 2) price, 3) similarity
        alternatives.sort(key=lambda x: (-x['brand_match'], x['price'], -x['similarity']))
        
        return alternatives
    
    def get_best_deal(
        self,
        product_name: str,
        current_market: str,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Get the single best deal (cheapest option) for a product.
        Returns None if no cheaper alternative found.
        """
        alternatives = self.find_same_product_in_other_markets(
            product_name, current_market, current_price
        )
        
        # Filter only cheaper options
        cheaper_options = [alt for alt in alternatives if alt['is_cheaper']]
        
        if cheaper_options:
            return cheaper_options[0]  # Already sorted by price
        
        return None
    
    def compare_cart_across_markets(
        self,
        cart_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare entire cart across all markets.
        Find which market offers the best total price.
        """
        market_totals = {}
        market_items = {}
        
        for item in cart_items:
            product_name = item['name']
            quantity = item['quantity']
            current_market = item['market']
            current_price = item['price']
            
            # Find alternatives
            alternatives = self.find_same_product_in_other_markets(
                product_name, current_market, current_price
            )
            
            # Calculate total for each market
            for alt in alternatives:
                market = alt['market']
                
                if market not in market_totals:
                    market_totals[market] = 0
                    market_items[market] = []
                
                market_totals[market] += alt['price'] * quantity
                market_items[market].append({
                    'name': alt['name'],
                    'price': alt['price'],
                    'quantity': quantity,
                    'subtotal': alt['price'] * quantity
                })
        
        # Find cheapest market
        if market_totals:
            cheapest_market = min(market_totals, key=market_totals.get)
            current_total = sum(item['price'] * item['quantity'] for item in cart_items)
            
            return {
                'current_total': current_total,
                'cheapest_market': cheapest_market,
                'cheapest_total': market_totals[cheapest_market],
                'savings': current_total - market_totals[cheapest_market],
                'all_markets': market_totals,
                'items_by_market': market_items
            }
        
        return {
            'current_total': sum(item['price'] * item['quantity'] for item in cart_items),
            'message': 'No alternatives found in other markets'
        }
    
    def get_price_comparison_summary(
        self,
        product_name: str,
        current_market: str,
        current_price: float,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get a comprehensive price comparison summary.
        """
        alternatives = self.find_same_product_in_other_markets(
            product_name, current_market, current_price
        )
        
        # Get top alternatives
        top_alternatives = alternatives[:limit]
        
        # Calculate statistics
        if alternatives:
            prices = [alt['price'] for alt in alternatives]
            cheapest = min(alternatives, key=lambda x: x['price'])
            most_expensive = max(alternatives, key=lambda x: x['price'])
            
            return {
                'product_name': product_name,
                'current_market': current_market,
                'current_price': current_price,
                'alternatives_found': len(alternatives),
                'cheapest_option': cheapest,
                'most_expensive_option': most_expensive,
                'average_price': sum(prices) / len(prices),
                'price_range': {
                    'min': min(prices),
                    'max': max(prices)
                },
                'top_alternatives': top_alternatives,
                'recommendation': cheapest if cheapest['is_cheaper'] else None
            }
        
        return {
            'product_name': product_name,
            'current_market': current_market,
            'current_price': current_price,
            'alternatives_found': 0,
            'message': 'No similar products found in other markets'
        }

# Singleton instance
price_comparison_service = PriceComparisonService()
