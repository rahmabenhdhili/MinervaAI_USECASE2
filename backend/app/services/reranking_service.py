"""
Re-ranking service to improve search results using multiple signals
"""
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import re

class RerankingService:
    """Re-rank search results using multiple signals"""
    
    def __init__(self):
        # Brand variations for better matching
        self.brand_variations = {
            'yab': ['yaourt', 'yogurt', 'yoghurt', 'yab'],
            'lilas': ['lila', 'lilac', 'lilas', 'lilass'],
            'delice': ['delice', 'délice', 'delice'],
            'vitalait': ['vital', 'vita', 'vitalait'],
            'sicam': ['sicam', 'sica'],
            'vidal': ['vidal', 'videl'],
            'garnier': ['garnier', 'garner'],
            'loreal': ['loreal', "l'oreal", 'l oreal'],
        }
        
        # Product type variations
        self.product_types = {
            'yaourt': ['yogurt', 'yoghurt', 'yaourt', 'yog'],
            'lait': ['milk', 'lben', 'leben', 'lait'],
            'fromage': ['cheese', 'jben', 'fromage'],
            'jus': ['juice', 'jus'],
            'eau': ['water', 'eau'],
            'huile': ['oil', 'huile', 'zit'],
            'savon': ['soap', 'savon', 'saboun'],
            'shampoing': ['shampoo', 'shampoing', 'shampooing'],
            'cheveux': ['hair', 'cheveux', 'shaar'],
        }
        
        # Category keywords for filtering
        self.category_keywords = {
            'hair_care': ['cheveux', 'hair', 'shampoo', 'shampoing', 'huile', 'oil', 'conditioner'],
            'body_care': ['savon', 'soap', 'gel', 'douche', 'shower', 'body'],
            'dairy': ['yaourt', 'yogurt', 'lait', 'milk', 'fromage', 'cheese'],
            'beverages': ['jus', 'juice', 'eau', 'water'],
        }
    
    def rerank(
        self,
        results: List[Dict],
        ocr_text: Optional[str] = None,
        user_preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Re-rank results using multiple signals
        
        Args:
            results: List of search results from Qdrant
            ocr_text: OCR extracted text from query image
            user_preferences: User preferences (favorite brands, etc.)
            
        Returns:
            Re-ranked results with updated scores
        """
        if not results:
            return results
        
        for result in results:
            base_score = result.get('score', 0.5)
            payload = result.get('payload', {})
            
            # Start with base visual similarity
            final_score = base_score
            
            # Signal 1: Text similarity (if OCR available)
            if ocr_text:
                text_score = self._calculate_text_similarity(
                    ocr_text,
                    payload.get('name', ''),
                    payload.get('description', ''),
                    payload.get('brand', '')
                )
                # Weighted combination: 60% visual + 40% text
                final_score = 0.6 * base_score + 0.4 * text_score
            
            # Signal 2: Brand match boost
            if ocr_text and payload.get('brand'):
                if self._has_brand_match(ocr_text, payload['brand']):
                    final_score *= 1.2  # 20% boost
            
            # Signal 3: Category match boost
            if ocr_text:
                if self._has_category_match(ocr_text, payload.get('category', '')):
                    final_score *= 1.1  # 10% boost
                else:
                    # Check for category mismatch penalty
                    query_category = self._detect_category(ocr_text)
                    product_category = self._detect_category(payload.get('name', '') + ' ' + payload.get('description', ''))
                    
                    if query_category and product_category and query_category != product_category:
                        final_score *= 0.5  # 50% penalty for wrong category!
            
            # Signal 4: Price reasonableness
            price = payload.get('price', 0)
            if self._is_price_reasonable(price):
                final_score *= 1.05  # 5% boost
            
            # Signal 5: User preferences
            if user_preferences:
                if payload.get('brand') in user_preferences.get('favorite_brands', []):
                    final_score *= 1.15  # 15% boost
            
            # Store final score
            result['final_score'] = min(final_score, 1.0)  # Cap at 1.0
            result['reranked'] = True
        
        # Sort by final score
        return sorted(results, key=lambda x: x.get('final_score', 0), reverse=True)
    
    def _calculate_text_similarity(
        self,
        query_text: str,
        product_name: str,
        product_description: str,
        product_brand: str
    ) -> float:
        """Calculate text similarity score"""
        query_lower = query_text.lower()
        
        # Combine product text fields
        product_text = f"{product_name} {product_description} {product_brand}".lower()
        
        # Method 1: Direct substring match
        if query_lower in product_text or product_name.lower() in query_lower:
            return 0.9
        
        # Method 2: Token overlap
        query_tokens = set(self._tokenize(query_lower))
        product_tokens = set(self._tokenize(product_text))
        
        if query_tokens and product_tokens:
            overlap = len(query_tokens & product_tokens)
            union = len(query_tokens | product_tokens)
            jaccard = overlap / union if union > 0 else 0
            
            if jaccard > 0.3:
                return 0.7 + (jaccard * 0.3)  # 0.7 to 1.0
        
        # Method 3: Sequence matching
        similarity = SequenceMatcher(None, query_lower, product_name.lower()).ratio()
        
        return similarity
    
    def _has_brand_match(self, query_text: str, brand: str) -> bool:
        """Check if query mentions the brand"""
        query_lower = query_text.lower()
        brand_lower = brand.lower()
        
        # Direct match
        if brand_lower in query_lower:
            return True
        
        # Check variations
        for key, variations in self.brand_variations.items():
            if brand_lower in variations or brand_lower == key:
                for variant in variations:
                    if variant in query_lower:
                        return True
        
        return False
    
    def _has_category_match(self, query_text: str, category: str) -> bool:
        """Check if query mentions the product category"""
        query_lower = query_text.lower()
        category_lower = category.lower()
        
        # Direct match
        if category_lower in query_lower:
            return True
        
        # Check product type variations
        for key, variations in self.product_types.items():
            if category_lower in variations or category_lower == key:
                for variant in variations:
                    if variant in query_lower:
                        return True
        
        return False
    
    def _detect_category(self, text: str) -> Optional[str]:
        """Detect product category from text"""
        text_lower = text.lower()
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return None
    
    def _is_price_reasonable(self, price: float) -> bool:
        """Check if price is in reasonable range"""
        # Most supermarket products are between 0.5 and 50 TND
        return 0.5 <= price <= 50.0
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove special characters and split
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Filter out very short tokens
        return [t for t in tokens if len(t) > 2]
    
    def expand_query(self, query_text: str) -> str:
        """
        Expand query with synonyms and variations
        
        Args:
            query_text: Original query text
            
        Returns:
            Expanded query text
        """
        tokens = self._tokenize(query_text.lower())
        expansions = set([query_text])
        
        for token in tokens:
            # Add brand variations
            for key, variations in self.brand_variations.items():
                if token == key or token in variations:
                    expansions.update(variations)
            
            # Add product type variations
            for key, variations in self.product_types.items():
                if token == key or token in variations:
                    expansions.update(variations)
        
        return ' '.join(expansions)

# Singleton instance
reranking_service = RerankingService()
