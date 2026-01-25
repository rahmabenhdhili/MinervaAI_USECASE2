import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Create client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

try:
    # Get list of collections (just tests the connection)
    collections = client.get_collections()
    print("✅ Connected! Collections:")
    print(collections)
except Exception as e:
    print("❌ Connection failed:")
    print(e)
