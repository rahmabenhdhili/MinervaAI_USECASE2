from fastembed import TextEmbedding
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

COLLECTION_NAME = "B2B"
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

def search_products(query: str, limit: int = 5):
    query_vector = list(embedding_model.embed([query]))[0]

    # Semantic search
    result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector.tolist(),
        with_payload=True,
        limit=limit
    )

    print(f"\n🔍 Results for: '{query}'\n")
    print("RAW RESULT:", result)

if __name__ == "__main__":
    search_products("ordinateur")
