from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, QueryRequest
from typing import List, Optional, Dict, Any
from uuid import uuid4
from models import Product
from config import get_settings


class QdrantService:
    """Service pour interagir avec Qdrant Cloud"""
    
    def __init__(self):
        settings = get_settings()
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.collection_name = settings.collection_name
        self.vector_size = settings.embedding_dimension
    
    async def initialize_collection(self):
        """Initialise la collection Qdrant si elle n'existe pas"""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Collection '{self.collection_name}' créée")
        else:
            print(f"✅ Collection '{self.collection_name}' existe déjà")
    
    async def store_product(
        self, 
        product: Product, 
        embedding: List[float]
    ) -> str:
        """Stocke un produit avec son embedding"""
        
        point_id = str(uuid4())
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "product_id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "url": product.url,
                "image_url": product.image_url,
                "rating": product.rating,
                "category": product.category,
                "metadata": product.metadata or {}
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        return point_id
    
    async def store_products_batch(
        self, 
        products: List[Product], 
        embeddings: List[List[float]]
    ) -> List[str]:
        """Stocke plusieurs produits en batch"""
        
        points = []
        point_ids = []
        
        for product, embedding in zip(products, embeddings):
            point_id = str(uuid4())
            point_ids.append(point_id)
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "product_id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "url": product.url,
                    "image_url": product.image_url,
                    "rating": product.rating,
                    "category": product.category,
                    "metadata": product.metadata or {}
                }
            ))
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return point_ids
    
    async def search_similar_products(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Recherche sémantique par similarité cosinus"""
        
        # Utiliser la méthode correcte selon la version de qdrant-client
        try:
            # Essayer avec query (nouvelle API)
            from qdrant_client.models import QueryRequest
            
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results.points
            ]
        except:
            # Fallback vers l'ancienne API si disponible
            try:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    score_threshold=score_threshold
                )
                
                return [
                    {
                        "id": result.id,
                        "score": result.score,
                        "payload": result.payload
                    }
                    for result in results
                ]
            except Exception as e:
                print(f"❌ Erreur Qdrant search: {e}")
                raise
    
    async def delete_collection(self):
        """Supprime la collection (utile pour les tests)"""
        self.client.delete_collection(collection_name=self.collection_name)
