from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from typing import List, Dict
import uuid
import os
from dotenv import load_dotenv


# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))


QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

class EmbeddingAgent:
    def __init__(self):
        self.embedding_model = TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5"
        )

        self.qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=30
        )

        self.collection_name = "B2B"

    def generate_embedding_text(self, product: Dict) -> str:
        return f"{product['product_name']} {product['category']} {product['brand']}"

    def index_products(self, products: List[Dict]):
        texts = [self.generate_embedding_text(p) for p in products]
        embeddings = list(self.embedding_model.embed(texts))

        points = []
        for product, embedding in zip(products, embeddings):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload=product
                )
            )

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        print(f"✅ {len(points)} products embedded and indexed")
