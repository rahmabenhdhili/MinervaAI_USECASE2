"""
Qdrant Memory Service - Recherche vectorielle TEMPORAIRE en mémoire

⚠️ IMPORTANT - CONFORMITÉ AUDIT:
- Qdrant fonctionne en mode :memory: UNIQUEMENT
- AUCUNE donnée n'est persistée sur disque
- Les collections sont créées à la volée et SUPPRIMÉES après usage
- Les produits scrapés ne sont JAMAIS stockés de façon permanente

Ce service est conçu pour être auditable et conforme aux exigences
de non-persistance des données scrapées.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    ScoredPoint
)
from typing import List, Dict, Any
from uuid import uuid4
import time


class QdrantMemoryService:
    """
    Service Qdrant en mode MÉMOIRE UNIQUEMENT
    
    ⚠️ AUDIT COMPLIANCE:
    - Mode: :memory: (pas de persistance disque)
    - Collections: Temporaires, supprimées après usage
    - Données: Éphémères, perdues à l'arrêt
    """
    
    def __init__(self):
        """
        Initialise Qdrant en mode :memory:
        
        ⚠️ CRITIQUE: location=":memory:" garantit qu'aucune donnée
        n'est écrite sur disque. Tout est en RAM uniquement.
        """
        print("🗄️ Initialisation Qdrant en mode :memory:")
        
        # AUDIT: Qdrant en mémoire uniquement - AUCUNE persistance
        self.client = QdrantClient(location=":memory:")
        
        print("✅ Qdrant initialisé en RAM (mode éphémère)")
    
    def create_temporary_collection(
        self, 
        collection_name: str, 
        vector_size: int
    ) -> None:
        """
        Crée une collection TEMPORAIRE en mémoire
        
        ⚠️ AUDIT: Cette collection existe uniquement en RAM
        et sera supprimée explicitement après usage.
        
        Args:
            collection_name: Nom unique de la collection temporaire
            vector_size: Dimension des vecteurs d'embeddings
        """
        print(f"📦 Création collection TEMPORAIRE: '{collection_name}'")
        print(f"   Dimension: {vector_size}D")
        print(f"   ⚠️ AUDIT: Collection en RAM uniquement (éphémère)")
        
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE  # Similarité cosinus
            )
        )
        
        print(f"✅ Collection '{collection_name}' créée en mémoire")
    
    def insert_products_temporary(
        self,
        collection_name: str,
        products: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        Insère des produits TEMPORAIREMENT dans Qdrant
        
        ⚠️ AUDIT: Les produits sont stockés en RAM uniquement
        pour la durée de la recherche, puis supprimés.
        
        Args:
            collection_name: Nom de la collection temporaire
            products: Liste des produits (métadonnées)
            embeddings: Vecteurs d'embeddings correspondants
            
        Returns:
            Nombre de produits insérés
        """
        print(f"💾 Insertion TEMPORAIRE de {len(products)} produits dans Qdrant")
        print(f"   ⚠️ AUDIT: Données en RAM uniquement, seront supprimées")
        
        points = []
        for product, embedding in zip(products, embeddings):
            point_id = str(uuid4())
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=product  # Métadonnées du produit
            ))
        
        # Insertion batch dans Qdrant (en mémoire)
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        print(f"✅ {len(points)} produits insérés en mémoire")
        return len(points)
    
    def search_similar_products(
        self,
        collection_name: str,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Recherche sémantique dans Qdrant (en mémoire)
        
        ⚠️ AUDIT: La recherche s'effectue sur des données
        temporaires en RAM uniquement.
        
        Args:
            collection_name: Nom de la collection temporaire
            query_embedding: Vecteur de la requête utilisateur
            limit: Nombre maximum de résultats
            score_threshold: Score minimum de similarité
            
        Returns:
            Liste des produits les plus similaires avec scores
        """
        print(f"🔍 Recherche sémantique dans Qdrant (mémoire)")
        print(f"   Top-{limit} résultats, seuil: {score_threshold}")
        
        start_time = time.time()
        
        # Recherche vectorielle avec Qdrant
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        search_time = (time.time() - start_time) * 1000
        print(f"✅ Recherche terminée en {search_time:.2f}ms")
        print(f"   {len(results)} produits trouvés")
        
        # Formater les résultats
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "score": result.score,
                "product": result.payload
            })
        
        return formatted_results
    
    def delete_temporary_collection(self, collection_name: str) -> None:
        """
        Supprime la collection temporaire de la mémoire
        
        ⚠️ AUDIT: Nettoyage explicite des données éphémères.
        Cette étape garantit qu'aucune donnée ne persiste.
        
        Args:
            collection_name: Nom de la collection à supprimer
        """
        print(f"🗑️ Suppression collection TEMPORAIRE: '{collection_name}'")
        print(f"   ⚠️ AUDIT: Nettoyage des données éphémères")
        
        try:
            self.client.delete_collection(collection_name=collection_name)
            print(f"✅ Collection '{collection_name}' supprimée de la mémoire")
            print(f"   ⚠️ AUDIT: Aucune donnée ne persiste")
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression: {e}")
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Récupère les informations d'une collection (debug)
        
        Args:
            collection_name: Nom de la collection
            
        Returns:
            Informations sur la collection
        """
        try:
            info = self.client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "status": info.status,
                "vectors_count": info.vectors_count
            }
        except Exception as e:
            return {"error": str(e)}
