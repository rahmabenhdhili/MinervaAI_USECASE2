from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
import pandas as pd
import uuid
from typing import List, Dict, Any, Optional
from .config import settings
from .models import Product
import logging
from functools import lru_cache
import asyncio

logger = logging.getLogger(__name__)

class QdrantDatabase:
    def __init__(self):
        # Connexion à Qdrant Cloud
        if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
            raise ValueError("QDRANT_URL et QDRANT_API_KEY doivent être configurés pour Qdrant Cloud")
        
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=300,  # Augmenter le timeout à 5 minutes
        )
        
        # Initialiser FastEmbed de manière lazy
        self.embedding_model = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        
        logger.info(f"Connexion à Qdrant Cloud établie: {settings.QDRANT_URL}")
    
    def _get_embedding_model(self):
        """Charge le modèle FastEmbed de manière lazy"""
        if self.embedding_model is None:
            logger.info("⚙️ Chargement du modèle FastEmbed...")
            # Utiliser le modèle par défaut de FastEmbed (BAAI/bge-small-en-v1.5)
            self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("✅ Modèle FastEmbed chargé")
        return self.embedding_model
        
    async def initialize_collection(self):
        """Initialise la collection Qdrant si elle n'existe pas"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"⚙️ Création de la collection '{self.collection_name}'...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # Dimension pour BAAI/bge-small-en-v1.5
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Collection '{self.collection_name}' créée")
            else:
                logger.info(f"✅ Collection '{self.collection_name}' existe déjà")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation de la collection: {e}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Crée un embedding pour un texte donné avec FastEmbed"""
        model = self._get_embedding_model()
        # FastEmbed retourne un générateur, on prend le premier résultat
        embeddings = list(model.embed([text]))
        return embeddings[0].tolist()
    
    def create_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        """Crée des embeddings pour plusieurs textes en batch avec FastEmbed (optimisé)"""
        model = self._get_embedding_model()
        logger.info(f"⚡ Création de {len(texts)} embeddings en batch avec FastEmbed...")
        # FastEmbed est déjà optimisé pour le batch processing
        embeddings = list(model.embed(texts))
        return [emb.tolist() for emb in embeddings]
    
    def prepare_product_text(self, product: Product) -> str:
        """Prépare le texte d'un produit pour l'embedding (optimisé)"""
        # Texte optimisé pour la recherche sémantique
        return f"{product.name} {product.brand} {product.category} {product.description[:200]}"
    
    async def add_products(self, products: List[Product]) -> Dict[str, Any]:
        """
        Ajoute des produits à la base vectorielle avec optimisation batch
        Retourne des statistiques détaillées
        """
        stats = {
            "total": len(products),
            "success": 0,
            "failed": 0,
            "steps": []
        }
        
        try:
            stats["steps"].append(f"📦 Préparation de {len(products)} produits...")
            
            # Étape 1: Préparer les textes pour embeddings
            stats["steps"].append("📝 Préparation des textes...")
            texts = [self.prepare_product_text(product) for product in products]
            stats["steps"].append(f"✅ {len(texts)} textes préparés")
            
            # Étape 2: Créer les embeddings en batch (optimisé)
            stats["steps"].append("🧠 Génération des embeddings (batch processing)...")
            embeddings = self.create_embedding_batch(texts)
            stats["steps"].append(f"✅ {len(embeddings)} embeddings générés")
            
            # Étape 3: Préparer les points pour Qdrant
            stats["steps"].append("🔧 Préparation des points Qdrant...")
            points = []
            for i, product in enumerate(products):
                product_id = str(uuid.uuid4())
                product.id = product_id
                
                point = PointStruct(
                    id=product_id,
                    vector=embeddings[i],
                    payload=product.dict()
                )
                points.append(point)
            
            stats["steps"].append(f"✅ {len(points)} points préparés")
            
            # Étape 4: Upload vers Qdrant en batch avec retry
            stats["steps"].append("☁️ Upload vers Qdrant Cloud...")
            batch_size = 50  # Réduire la taille des batches pour éviter les timeouts
            total_batches = (len(points) - 1) // batch_size + 1
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                # Retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.client.upsert(
                            collection_name=self.collection_name,
                            points=batch,
                            wait=True  # Attendre la confirmation
                        )
                        stats["steps"].append(f"  ↗️ Batch {batch_num}/{total_batches} uploadé ({len(batch)} produits)")
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ Erreur batch {batch_num}, tentative {attempt + 1}/{max_retries}: {e}")
                            stats["steps"].append(f"  ⚠️ Retry batch {batch_num}...")
                            import time
                            time.sleep(2)  # Attendre 2 secondes avant de réessayer
                        else:
                            logger.error(f"❌ Échec batch {batch_num} après {max_retries} tentatives")
                            raise
            
            stats["success"] = len(products)
            stats["steps"].append(f"✅ {stats['success']} produits ajoutés à Qdrant Cloud")
            
            logger.info(f"✅ {len(products)} produits ajoutés avec succès")
            return stats
            
        except Exception as e:
            stats["failed"] = len(products)
            stats["steps"].append(f"❌ Erreur: {str(e)}")
            logger.error(f"❌ Erreur lors de l'ajout des produits: {e}")
            raise
    
    async def search_similar_products(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche des produits similaires avec FastEmbed"""
        try:
            # Créer l'embedding de la requête avec FastEmbed
            query_embedding = self.create_embedding(query)
            
            # Recherche dans Qdrant avec query_points (nouvelle API)
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            products = []
            for result in search_result.points:
                product_data = result.payload
                product_data['score'] = result.score
                products.append(product_data)
            
            logger.info(f"🔍 {len(products)} produits trouvés pour: '{query}'")
            return products
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Récupère un produit par son ID"""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[product_id]
            )
            
            if result:
                return result[0].payload
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération du produit: {e}")
            return None
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Récupère les informations sur la collection"""
        try:
            # Utiliser scroll pour compter les points (plus fiable)
            result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1,
                with_payload=False,
                with_vectors=False
            )
            
            # Compter tous les points
            count_result = self.client.count(
                collection_name=self.collection_name
            )
            
            return {
                "name": self.collection_name,
                "points_count": count_result.count,
                "status": "ready"
            }
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des infos: {e}")
            # Retourner une valeur par défaut
            return {
                "name": self.collection_name,
                "points_count": 0,
                "status": "unknown"
            }

# Instance globale
db = QdrantDatabase()