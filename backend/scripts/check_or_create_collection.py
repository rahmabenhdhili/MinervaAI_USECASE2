import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "B2B"
VECTOR_SIZE = 384

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

collections = client.get_collections().collections
exists = any(c.name == COLLECTION_NAME for c in collections)

if not exists:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print(f"✅ Collection '{COLLECTION_NAME}' created")
else:
    print(f"ℹ️ Collection '{COLLECTION_NAME}' already exists")
