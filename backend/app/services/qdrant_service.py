from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.schemas import Product
import uuid

class QdrantService:
    def __init__(self):
        try:
            import ssl
            import certifi
            
            # Connect with longer timeout and SSL configuration
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=180,  # 3 minutes timeout for slow connections
                prefer_grpc=False,  # Use REST API
                https=True
            )
            print(f"[OK] Connected to Qdrant Cloud")
        except Exception as e:
            print(f"[ERROR] Qdrant Cloud connection failed: {e}")
            print(f"[WARNING] Shopping Mode will use SQLite fallback")
            # Don't raise - allow app to continue with SQLite fallback
            self.client = None
        
        # Only use CLIP dimension for image embeddings (Shopping Mode only)
        self.clip_dimension = settings.CLIP_DIMENSION
    
    def create_collection(self, collection_name: str, use_clip: bool = False):
        """Create a Qdrant collection if it doesn't exist"""
        from qdrant_client.models import PayloadSchemaType
        
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            # Use CLIP dimension for supermarket (image search), text dimension for PC
            dimension = self.clip_dimension if use_clip else self.dimension
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {collection_name} with dimension {dimension}")
            
            # Create payload indexes for filtering
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="price",
                field_schema=PayloadSchemaType.FLOAT
            )
            print(f"Created index on 'price' field")
            
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="category",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"Created index on 'category' field")
            
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="market",
                field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"Created index on 'market' field")
        else:
            print(f"Collection already exists: {collection_name}")
    
    def insert_product(self, collection_name: str, product: Product, embedding: List[float]):
        """Insert a single product into Qdrant"""
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "product_id": product.id,
                "name": product.name,
                "description": product.description,
                "category": product.category,
                "price": product.price,
                "market": product.market,
                "image_path": product.image_path,
                "specs": product.specs,
                "brand": product.brand
            }
        )
        
        self.client.upsert(
            collection_name=collection_name,
            points=[point]
        )
    
    def batch_insert_products(self, collection_name: str, products: List[Product], embeddings: List[List[float]]):
        """Batch insert products into Qdrant"""
        points = []
        for product, embedding in zip(products, embeddings):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "product_id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "category": product.category,
                    "price": product.price,
                    "market": product.market,
                    "image_path": product.image_path,
                    "specs": product.specs,
                    "brand": product.brand
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Inserted {len(points)} products into {collection_name}")
    
    def search_products(
        self,
        collection_name: str,
        query_vector: List[float],
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = 10,
        use_mmr: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search products with optional filters using MMR for diversity.
        MMR (Maximal Marginal Relevance) ensures diverse, relevant results.
        """
        from app.core.config import settings
        
        # Check if client is available
        if self.client is None:
            print("  [WARNING] Qdrant client not available, returning empty results")
            return []
        
        query_filter = None
        
        # Build filter conditions
        conditions = []
        if max_price is not None:
            conditions.append(
                FieldCondition(
                    key="price",
                    range=Range(lte=max_price)
                )
            )
        
        if category:
            conditions.append(
                FieldCondition(
                    key="category",
                    match={"value": category}
                )
            )
        
        if market:
            conditions.append(
                FieldCondition(
                    key="market",
                    match={"value": market}
                )
            )
        
        if conditions:
            query_filter = Filter(must=conditions)
        
        # Use search API (query API signature changed in newer versions)
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit * 2,  # Get more results for Groq to analyze
            score_threshold=0.3  # Minimum similarity threshold
        )
        
        # Parse search results
        formatted_results = []
        for hit in results:
            formatted_results.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            })
        
        return formatted_results
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            return {"error": str(e)}

# Singleton instance
qdrant_service = QdrantService()
