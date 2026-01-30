from scripts.embedding_agent_B2B import EmbeddingAgent

embedding_agent = EmbeddingAgent()
client = embedding_agent.qdrant_client
collection_name = embedding_agent.collection_name

def query_personalized_products(user_text: str, top_k: int = 5):
    """
    Convert user preference text into vector and query Qdrant.
    """

    vector = list(
        embedding_agent.embedding_model.embed([user_text])
    )[0]

    response = client.query_points(
        collection_name=collection_name,
        query=vector.tolist(),
        with_payload=True,
        limit=top_k
    )

    results = []
    for hit in response.points:
        payload = hit.payload or {}
        results.append({
            "product_name": payload.get("product_name"),
            "brand": payload.get("brand"),
            "category": payload.get("category"),
            "supplier_name": payload.get("supplier_name"),
            "unit_price": payload.get("unit_price"),
            "score": float(hit.score)
        })

    return results
