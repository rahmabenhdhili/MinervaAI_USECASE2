"""
Caching service for Shopping Mode.
Caches image embeddings and search results to improve performance.
"""
import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

class CacheService:
    """
    In-memory cache with optional disk persistence.
    Caches:
    - Image embeddings (CLIP vectors)
    - Search results from Qdrant
    - Product data from SQLite
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(__file__).parent.parent.parent / cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory caches
        self.embedding_cache = {}  # image_hash -> embedding
        self.search_cache = {}     # query_hash -> results
        self.product_cache = {}    # product_id -> product_data
        
        # Cache TTL (time to live) in seconds
        self.embedding_ttl = 3600  # 1 hour
        self.search_ttl = 300      # 5 minutes
        self.product_ttl = 86400   # 24 hours
        
        print("✓ Cache service initialized")
    
    def _hash_image(self, image_bytes: bytes) -> str:
        """Generate hash for image bytes"""
        return hashlib.sha256(image_bytes).hexdigest()
    
    def _hash_query(self, market: str, budget: float, limit: int) -> str:
        """Generate hash for search query"""
        query_str = f"{market}_{budget}_{limit}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry is expired"""
        return (time.time() - timestamp) > ttl
    
    # ==================== IMAGE EMBEDDING CACHE ====================
    
    def get_embedding(self, image_bytes: bytes) -> Optional[List[float]]:
        """Get cached embedding for image"""
        image_hash = self._hash_image(image_bytes)
        
        if image_hash in self.embedding_cache:
            entry = self.embedding_cache[image_hash]
            
            # Check if expired
            if not self._is_expired(entry['timestamp'], self.embedding_ttl):
                print(f"  ✓ Cache HIT: Image embedding")
                return entry['embedding']
            else:
                # Remove expired entry
                del self.embedding_cache[image_hash]
        
        print(f"  ✗ Cache MISS: Image embedding")
        return None
    
    def set_embedding(self, image_bytes: bytes, embedding: List[float]):
        """Cache embedding for image"""
        image_hash = self._hash_image(image_bytes)
        
        self.embedding_cache[image_hash] = {
            'embedding': embedding,
            'timestamp': time.time()
        }
        
        print(f"  ✓ Cached image embedding")
    
    # ==================== SEARCH RESULTS CACHE ====================
    
    def get_search_results(
        self, 
        image_bytes: bytes,
        market: str, 
        budget: float, 
        limit: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        image_hash = self._hash_image(image_bytes)
        query_hash = self._hash_query(market, budget, limit)
        cache_key = f"{image_hash}_{query_hash}"
        
        if cache_key in self.search_cache:
            entry = self.search_cache[cache_key]
            
            # Check if expired
            if not self._is_expired(entry['timestamp'], self.search_ttl):
                print(f"  ✓ Cache HIT: Search results")
                return entry['results']
            else:
                # Remove expired entry
                del self.search_cache[cache_key]
        
        print(f"  ✗ Cache MISS: Search results")
        return None
    
    def set_search_results(
        self,
        image_bytes: bytes,
        market: str,
        budget: float,
        limit: int,
        results: List[Dict[str, Any]]
    ):
        """Cache search results"""
        image_hash = self._hash_image(image_bytes)
        query_hash = self._hash_query(market, budget, limit)
        cache_key = f"{image_hash}_{query_hash}"
        
        self.search_cache[cache_key] = {
            'results': results,
            'timestamp': time.time()
        }
        
        print(f"  ✓ Cached search results ({len(results)} items)")
    
    # ==================== PRODUCT DATA CACHE ====================
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get cached product data"""
        if product_id in self.product_cache:
            entry = self.product_cache[product_id]
            
            # Check if expired
            if not self._is_expired(entry['timestamp'], self.product_ttl):
                return entry['product']
            else:
                # Remove expired entry
                del self.product_cache[product_id]
        
        return None
    
    def set_product(self, product_id: str, product_data: Dict[str, Any]):
        """Cache product data"""
        self.product_cache[product_id] = {
            'product': product_data,
            'timestamp': time.time()
        }
    
    def set_products_batch(self, products: List[Dict[str, Any]]):
        """Cache multiple products at once"""
        for product in products:
            product_id = product.get('product_id') or product.get('id')
            if product_id:
                self.set_product(product_id, product)
    
    # ==================== CACHE MANAGEMENT ====================
    
    def clear_expired(self):
        """Remove all expired cache entries"""
        # Clear expired embeddings
        expired_embeddings = [
            k for k, v in self.embedding_cache.items()
            if self._is_expired(v['timestamp'], self.embedding_ttl)
        ]
        for k in expired_embeddings:
            del self.embedding_cache[k]
        
        # Clear expired search results
        expired_searches = [
            k for k, v in self.search_cache.items()
            if self._is_expired(v['timestamp'], self.search_ttl)
        ]
        for k in expired_searches:
            del self.search_cache[k]
        
        # Clear expired products
        expired_products = [
            k for k, v in self.product_cache.items()
            if self._is_expired(v['timestamp'], self.product_ttl)
        ]
        for k in expired_products:
            del self.product_cache[k]
        
        total_cleared = len(expired_embeddings) + len(expired_searches) + len(expired_products)
        if total_cleared > 0:
            print(f"✓ Cleared {total_cleared} expired cache entries")
    
    def clear_all(self):
        """Clear all caches"""
        self.embedding_cache.clear()
        self.search_cache.clear()
        self.product_cache.clear()
        print("✓ Cleared all caches")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "embedding_cache_size": len(self.embedding_cache),
            "search_cache_size": len(self.search_cache),
            "product_cache_size": len(self.product_cache),
            "total_entries": len(self.embedding_cache) + len(self.search_cache) + len(self.product_cache)
        }
    
    def save_to_disk(self):
        """Persist cache to disk (optional)"""
        cache_file = self.cache_dir / "cache.pkl"
        
        cache_data = {
            'embedding_cache': self.embedding_cache,
            'search_cache': self.search_cache,
            'product_cache': self.product_cache
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        
        print(f"✓ Cache saved to {cache_file}")
    
    def load_from_disk(self):
        """Load cache from disk (optional)"""
        cache_file = self.cache_dir / "cache.pkl"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.embedding_cache = cache_data.get('embedding_cache', {})
            self.search_cache = cache_data.get('search_cache', {})
            self.product_cache = cache_data.get('product_cache', {})
            
            # Clear expired entries after loading
            self.clear_expired()
            
            print(f"✓ Cache loaded from {cache_file}")
        else:
            print("ℹ️ No cache file found")

# Singleton instance
cache_service = CacheService()
