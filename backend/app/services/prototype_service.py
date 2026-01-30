"""
Prototype-based Few-Shot Learning Service
Creates category/brand prototypes for better matching with limited data
"""
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict
import pickle
from pathlib import Path

class PrototypeService:
    """
    Few-shot learning using prototypes.
    Each category/brand gets a prototype embedding (average of all examples).
    Query is first matched to prototypes, then to specific products.
    """
    
    def __init__(self):
        self.prototypes = {}  # {category: {brand: prototype_embedding}}
        self.prototype_counts = {}  # Track number of examples per prototype
        self.cache_path = Path(__file__).parent.parent.parent / "cache" / "prototypes.pkl"
        self.load_prototypes()
    
    def create_prototypes(self, products_data: List[Dict]) -> Dict:
        """
        Create prototype embeddings for each category-brand combination.
        
        Args:
            products_data: List of dicts with 'category', 'brand', 'embedding'
            
        Returns:
            Dictionary of prototypes
        """
        print("\n🎯 Creating Few-Shot Prototypes...")
        
        # Group embeddings by category and brand
        groups = defaultdict(lambda: defaultdict(list))
        
        for product in products_data:
            category = product.get('category', 'unknown')
            brand = product.get('brand', 'unknown')
            embedding = product.get('embedding')
            
            if embedding:
                groups[category][brand].append(embedding)
        
        # Calculate prototype (mean) for each group
        prototypes = {}
        counts = {}
        
        for category, brands in groups.items():
            prototypes[category] = {}
            counts[category] = {}
            
            for brand, embeddings in brands.items():
                if embeddings:
                    # Calculate mean embedding (prototype)
                    prototype = np.mean(embeddings, axis=0)
                    # Normalize
                    prototype = prototype / np.linalg.norm(prototype)
                    
                    prototypes[category][brand] = prototype.tolist()
                    counts[category][brand] = len(embeddings)
        
        self.prototypes = prototypes
        self.prototype_counts = counts
        
        # Print statistics
        total_prototypes = sum(len(brands) for brands in prototypes.values())
        print(f"  ✓ Created {total_prototypes} prototypes")
        print(f"  ✓ Categories: {len(prototypes)}")
        
        for category, brands in sorted(prototypes.items()):
            total_examples = sum(counts[category].values())
            print(f"    - {category}: {len(brands)} brands, {total_examples} examples")
        
        # Save to cache
        self.save_prototypes()
        
        return prototypes
    
    def find_closest_prototype(
        self,
        query_embedding: List[float],
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find the closest prototypes to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of closest prototypes to return
            
        Returns:
            List of {category, brand, similarity, count}
        """
        if not self.prototypes:
            return []
        
        query_vec = np.array(query_embedding)
        results = []
        
        for category, brands in self.prototypes.items():
            for brand, prototype in brands.items():
                proto_vec = np.array(prototype)
                
                # Cosine similarity
                similarity = np.dot(query_vec, proto_vec)
                
                results.append({
                    'category': category,
                    'brand': brand,
                    'similarity': float(similarity),
                    'count': self.prototype_counts[category][brand]
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def get_category_filter(
        self,
        query_embedding: List[float],
        threshold: float = 0.6
    ) -> Optional[str]:
        """
        Get the most likely category for filtering.
        
        Args:
            query_embedding: Query embedding
            threshold: Minimum similarity threshold
            
        Returns:
            Category name or None
        """
        prototypes = self.find_closest_prototype(query_embedding, top_k=1)
        
        if prototypes and prototypes[0]['similarity'] >= threshold:
            return prototypes[0]['category']
        
        return None
    
    def boost_score_by_prototype(
        self,
        query_embedding: List[float],
        product_category: str,
        product_brand: str,
        base_score: float
    ) -> float:
        """
        Boost product score if it matches the closest prototype.
        
        Args:
            query_embedding: Query embedding
            product_category: Product's category
            product_brand: Product's brand
            base_score: Base similarity score
            
        Returns:
            Boosted score
        """
        closest = self.find_closest_prototype(query_embedding, top_k=1)
        
        if not closest:
            return base_score
        
        top_proto = closest[0]
        
        # Boost if category matches
        if product_category == top_proto['category']:
            boost = 0.1  # 10% boost
            
            # Extra boost if brand also matches
            if product_brand == top_proto['brand']:
                boost = 0.2  # 20% boost
            
            return min(base_score + boost, 1.0)
        
        return base_score
    
    def save_prototypes(self):
        """Save prototypes to cache"""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'prototypes': self.prototypes,
                'counts': self.prototype_counts
            }
            
            with open(self.cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"  ✓ Prototypes saved to cache")
        except Exception as e:
            print(f"  ⚠️ Failed to save prototypes: {e}")
    
    def load_prototypes(self):
        """Load prototypes from cache"""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'rb') as f:
                    data = pickle.load(f)
                
                self.prototypes = data.get('prototypes', {})
                self.prototype_counts = data.get('counts', {})
                
                total = sum(len(brands) for brands in self.prototypes.values())
                if total > 0:
                    print(f"✓ Loaded {total} prototypes from cache")
        except Exception as e:
            print(f"⚠️ Failed to load prototypes: {e}")
            self.prototypes = {}
            self.prototype_counts = {}

# Singleton instance
prototype_service = PrototypeService()
