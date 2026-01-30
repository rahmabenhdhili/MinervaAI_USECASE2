from typing import List, Dict

class SemanticSearchAgent:
    def __init__(self, embedding_agent):
        self.embedding_agent = embedding_agent
        self.qdrant_client = embedding_agent.qdrant_client
        self.collection_name = embedding_agent.collection_name

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic search for relevant products"""
        # Embed the query
        query_embedding = list(self.embedding_agent.embedding_model.embed([query]))[0]

        response = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            with_payload=True,
            limit=top_k
        )

        # response is a list of tuples: (score, points_list)
        results: List[Dict] = []

        for hit in response.points:
            payload = hit.payload or {}
            results.append({
                "product_name": payload.get("product_name"),
                "category": payload.get("category"),
                "brand": payload.get("brand"),
                "supplier_name": payload.get("supplier_name"),
                "city": payload.get("city"),
                "phone": payload.get("phone"),
                "email": payload.get("email"),
                "unit_price": float(payload.get("unit_price")),
                "similarity_score": float(hit.score),
            })

        return results
