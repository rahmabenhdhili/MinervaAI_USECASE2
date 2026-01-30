"""
Hybrid search service combining SigLIP visual similarity with text matching.
Improves accuracy by considering both image and product name.
Uses SigLIP for all embeddings (Shopping Mode).
"""
from typing import List, Dict, Any
from app.services.siglip_service import siglip_service
from app.services.qdrant_service import qdrant_service
from difflib import SequenceMatcher
import numpy as np

class HybridSearchService:
    """
    Combines visual (SigLIP) and textual (name/brand) similarity.
    Uses simple string matching for text (no embedding overhead).
    """
    
    def __init__(self):
        self.visual_weight = 0.7  # 70% visual similarity (primary)
        self.text_weight = 0.3    # 30% text similarity (secondary)
        self.use_text_embedding = False  # Disabled to avoid memory issues
    
    def _calculate_text_similarity(self, query_text: str, product_name: str) -> float:
        """Calculate text similarity between query and product name"""
        query_text = query_text.lower().strip()
        product_name = product_name.lower().strip()
        
        return SequenceMatcher(None, query_text, product_name).ratio()
    
    def _calculate_clip_text_similarity(
        self, 
        query_text: str, 
        image_embedding: List[float]
    ) -> float:
        """
        Calculate similarity using CLIP text embeddings (multimodal!)
        
        This is the magic: CLIP embeds text into the SAME space as images,
        so we can directly compare text with image embeddings!
        """
        try:
            # Embed query text using CLIP
            text_embedding = clip_service.embed_text(query_text)
            
            # Calculate cosine similarity with image embedding
            # Both are in the same 512-dimensional space!
            similarity = self._cosine_similarity(text_embedding, image_embedding)
            
            return similarity
        except Exception as e:
            print(f"⚠️ CLIP text embedding failed: {e}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _extract_brand_from_name(self, name: str) -> str:
        """Extract brand (usually first word)"""
        words = name.split()
        return words[0] if words else ""
    
    def _build_product_text(
        self,
        name: str,
        description: str = "",
        brand: str = "",
        category: str = ""
    ) -> str:
        """
        Build comprehensive product text for better matching.
        
        Combines: name + description + brand + category
        
        Example:
        - Name: "LBM Sablé aux amandes 200g"
        - Description: "Biscuits sablés aux amandes"
        - Brand: "LBM"
        - Category: "biscuits"
        
        Result: "LBM Sablé aux amandes 200g Biscuits sablés aux amandes LBM biscuits"
        
        This helps CLIP understand the full context of the product!
        """
        parts = []
        
        # Always include name (most important)
        if name:
            parts.append(name)
        
        # Add description (provides context)
        if description and description.lower() not in name.lower():
            parts.append(description)
        
        # Add brand (helps with brand-specific searches)
        if brand and brand.lower() not in name.lower():
            parts.append(brand)
        
        # Add category (helps with category searches like "biscuits", "yaourt")
        if category:
            parts.append(category)
        
        # Join with spaces
        full_text = " ".join(parts)
        
        return full_text
    
    def hybrid_search(
        self,
        image_embedding: List[float],
        query_text: str,
        collection_name: str,
        market: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining visual and text similarity.
        
        Simplified: Uses visual search + string matching (no text embeddings)
        
        Steps:
        1. Get visual matches from Qdrant
        2. Calculate text similarity using string matching
        3. Combine scores with weights
        4. Re-rank results
        """
        # Step 1: Get visual matches
        visual_results = qdrant_service.search_products(
            collection_name=collection_name,
            query_vector=image_embedding,
            max_price=None,
            category=None,
            market=market,
            limit=limit * 2,  # Get 2x for re-ranking
            use_mmr=False  # Disable MMR for pure similarity
        )
        
        # Step 2: Calculate text similarity using CLIP multimodal embeddings
        hybrid_results = []
        
        for result in visual_results:
            payload = result["payload"]
            product_name = payload["name"]
            product_description = payload.get("description", "")
            product_brand = payload.get("brand", "")
            product_category = payload.get("category", "")
            visual_score = result.get("score", 0)
            
            # Build comprehensive product text (name + description + brand + category)
            product_full_text = self._build_product_text(
                name=product_name,
                description=product_description,
                brand=product_brand,
                category=product_category
            )
            
            # Method 1: CLIP multimodal similarity (NEW!)
            if self.use_clip_text and query_text:
                # Use CLIP to embed the FULL product text (not just name)
                product_text_embedding = clip_service.embed_text(product_full_text)
                
                # Compare query text embedding with product text embedding
                text_score = self._calculate_clip_text_similarity(
                    query_text, 
                    product_text_embedding
                )
                
                print(f"  🔍 CLIP multimodal: '{product_name[:40]}' = {text_score:.2f}")
            else:
                # Fallback: String matching with full text
                text_score = self._calculate_text_similarity(query_text, product_full_text)
            
            # Boost if brand matches
            query_brand = self._extract_brand_from_name(query_text)
            product_brand = payload.get("brand", "")
            
            if query_brand and product_brand:
                if query_brand.lower() in product_brand.lower():
                    text_score = min(1.0, text_score + 0.2)  # Boost by 20%
            
            # Combine scores
            hybrid_score = (
                self.visual_weight * visual_score +
                self.text_weight * text_score
            )
            
            hybrid_results.append({
                **result,
                "visual_score": visual_score,
                "text_score": text_score,
                "hybrid_score": hybrid_score,
                "score": hybrid_score  # Override score with hybrid
            })
        
        # Step 3: Re-rank by hybrid score
        hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        # Return top results
        return hybrid_results[:limit]
    
    def search_by_text_only(
        self,
        query_text: str,
        collection_name: str,
        market: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search using ONLY text (no image)
        
        NEW: Uses CLIP to embed text and search in image space!
        This is the power of multimodal embeddings.
        """
        try:
            # Embed text using CLIP
            text_embedding = clip_service.embed_text(query_text)
            
            print(f"  🔍 Text-only search: '{query_text}'")
            
            # Search Qdrant using text embedding
            # This works because CLIP embeds text and images in the same space!
            results = qdrant_service.search_products(
                collection_name=collection_name,
                query_vector=text_embedding,  # Text vector searching image vectors!
                max_price=None,
                category=None,
                market=market,
                limit=limit * 2,
                use_mmr=False
            )
            
            return results[:limit]
            
        except Exception as e:
            print(f"❌ Text-only search failed: {e}")
            return []
    
    def search_with_text_hint(
        self,
        image_embedding: List[float],
        text_hint: str,
        collection_name: str,
        market: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search with optional text hint to improve accuracy.
        
        Use cases:
        - User types product name while uploading image
        - OCR extracts text from product label
        - Voice input provides product name
        """
        if text_hint:
            # Use hybrid search with CLIP multimodal
            return self.hybrid_search(
                image_embedding=image_embedding,
                query_text=text_hint,
                collection_name=collection_name,
                market=market,
                limit=limit
            )
        else:
            # Fall back to pure visual search
            results = qdrant_service.search_products(
                collection_name=collection_name,
                query_vector=image_embedding,
                max_price=None,
                category=None,
                limit=limit,
                use_mmr=True
            )
            
            # Filter by market
            return [r for r in results if r["payload"]["market"] == market]

# Singleton instance
hybrid_search_service = HybridSearchService()
