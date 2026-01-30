"""
Real-Time Semantic Search Service - Pipeline Complet

⚠️ ARCHITECTURE AUDIT-COMPLIANT:
1. Scraping temps réel (pas de cache)
2. Embeddings avec FastEmbed (Qdrant-compatible)
3. Qdrant en mode :memory: (éphémère)
4. Recherche sémantique vectorielle
5. Nettoyage explicite (suppression collection)

GARANTIES:
- AUCUNE persistance disque
- Données 100% temporaires (RAM uniquement)
- Collections supprimées après chaque recherche
- Produits scrapés jamais stockés de façon permanente
"""

from typing import List, Dict, Any
from uuid import uuid4
import time
import asyncio

from services.fastembed_service import FastEmbedService
from services.qdrant_memory_service import QdrantMemoryService
from services.product_scraper_service import ProductScraperService
from models import Product


class RealtimeSemanticSearchService:
    """
    Service de recherche sémantique en temps réel
    
    ⚠️ AUDIT COMPLIANCE:
    - Qdrant utilisé en mode :memory: uniquement
    - FastEmbed pour les embeddings
    - Aucune persistance des données scrapées
    - Collections temporaires supprimées après usage
    """
    
    def __init__(self):
        """Initialise les services nécessaires"""
        print("🚀 Initialisation du pipeline de recherche sémantique")
        print("=" * 60)
        
        # Service d'embeddings (FastEmbed)
        self.fastembed_service = FastEmbedService()
        
        # Service Qdrant en mémoire (éphémère)
        self.qdrant_service = QdrantMemoryService()
        
        # Service de scraping temps réel
        self.scraper_service = ProductScraperService()
        
        print("=" * 60)
        print("✅ Pipeline initialisé et prêt")
        print("⚠️ AUDIT: Mode éphémère activé (aucune persistance)")
        print()
    
    async def search_products_semantic(
        self,
        user_query: str,
        use_amazon: bool = True,
        use_alibaba: bool = True,
        use_walmart: bool = False,
        use_cdiscount: bool = False,
        max_results: int = 20,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Pipeline complet de recherche sémantique en temps réel
        
        ⚠️ AUDIT: Ce pipeline garantit qu'aucune donnée n'est persistée.
        
        ÉTAPES:
        1. Scraping temps réel (données fraîches)
        2. Génération embeddings (FastEmbed)
        3. Création collection temporaire (Qdrant :memory:)
        4. Insertion temporaire dans Qdrant
        5. Recherche sémantique vectorielle
        6. Suppression collection (nettoyage)
        
        Args:
            user_query: Requête utilisateur
            use_amazon: Scraper Amazon
            use_alibaba: Scraper Alibaba
            use_walmart: Scraper Walmart
            use_cdiscount: Scraper Cdiscount
            max_results: Nombre max de produits à scraper
            top_k: Nombre de résultats à retourner
            
        Returns:
            Résultats de recherche avec scores de similarité
        """
        pipeline_start = time.time()
        collection_name = f"temp_search_{uuid4().hex[:8]}"
        
        print("=" * 60)
        print("🔍 PIPELINE DE RECHERCHE SÉMANTIQUE EN TEMPS RÉEL")
        print("=" * 60)
        print(f"📝 Requête: '{user_query}'")
        print(f"🗄️ Collection temporaire: '{collection_name}'")
        print(f"⚠️ AUDIT: Données éphémères, seront supprimées")
        print()
        
        try:
            # ============================================================
            # ÉTAPE 1: SCRAPING TEMPS RÉEL
            # ⚠️ AUDIT: Produits scrapés en temps réel, pas de cache
            # ============================================================
            print("📦 ÉTAPE 1/6: Scraping temps réel des produits")
            print("-" * 60)
            
            scraping_start = time.time()
            products = await self.scraper_service.search_products(
                keywords=[user_query],
                max_results=max_results,
                use_amazon=use_amazon,
                use_alibaba=use_alibaba,
                use_walmart=use_walmart,
                use_cdiscount=use_cdiscount
            )
            scraping_time = time.time() - scraping_start
            
            print(f"✅ {len(products)} produits scrapés en {scraping_time:.2f}s")
            print(f"⚠️ AUDIT: Produits en mémoire uniquement (pas de stockage)")
            print()
            
            if not products:
                print("⚠️ Aucun produit trouvé")
                return {
                    "success": False,
                    "query": user_query,
                    "results": [],
                    "total_found": 0,
                    "message": "Aucun produit trouvé"
                }
            
            # ============================================================
            # ÉTAPE 2: NORMALISATION DES PRODUITS
            # ⚠️ AUDIT: Conversion en format unifié (temporaire)
            # ============================================================
            print("🔄 ÉTAPE 2/6: Normalisation des produits")
            print("-" * 60)
            
            normalized_products = []
            product_texts = []
            
            for product in products:
                # Format unifié pour tous les scrapers
                normalized = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description or "",
                    "price": product.price,
                    "url": product.url,
                    "image_url": product.image_url,
                    "source": product.metadata.get("source", "unknown"),
                    "category": product.category or ""
                }
                normalized_products.append(normalized)
                
                # Texte pour embedding
                text = self.fastembed_service.create_product_text(
                    name=product.name,
                    description=product.description or "",
                    category=product.category or ""
                )
                product_texts.append(text)
            
            print(f"✅ {len(normalized_products)} produits normalisés")
            print(f"⚠️ AUDIT: Données en RAM uniquement")
            print()
            
            # ============================================================
            # ÉTAPE 3: GÉNÉRATION EMBEDDINGS (FastEmbed)
            # ⚠️ AUDIT: Embeddings générés à la volée (pas de cache)
            # ============================================================
            print("🧠 ÉTAPE 3/6: Génération embeddings (FastEmbed)")
            print("-" * 60)
            
            embedding_start = time.time()
            
            # Embeddings des produits (batch)
            product_embeddings = self.fastembed_service.generate_embeddings_batch(
                product_texts
            )
            
            # Embedding de la requête
            query_embedding = self.fastembed_service.generate_embedding(user_query)
            
            embedding_time = time.time() - embedding_start
            
            print(f"✅ {len(product_embeddings)} embeddings générés")
            print(f"   Dimension: {len(query_embedding)}D")
            print(f"   Temps: {embedding_time:.2f}s")
            print(f"⚠️ AUDIT: Embeddings temporaires (RAM uniquement)")
            print()
            
            # ============================================================
            # ÉTAPE 4: CRÉATION COLLECTION TEMPORAIRE (Qdrant)
            # ⚠️ AUDIT: Collection en :memory: uniquement
            # ============================================================
            print("🗄️ ÉTAPE 4/6: Création collection temporaire (Qdrant)")
            print("-" * 60)
            
            self.qdrant_service.create_temporary_collection(
                collection_name=collection_name,
                vector_size=len(query_embedding)
            )
            print()
            
            # ============================================================
            # ÉTAPE 5: INSERTION TEMPORAIRE DANS QDRANT
            # ⚠️ AUDIT: Données insérées en RAM uniquement
            # ============================================================
            print("💾 ÉTAPE 5/6: Insertion temporaire dans Qdrant")
            print("-" * 60)
            
            insert_start = time.time()
            
            inserted_count = self.qdrant_service.insert_products_temporary(
                collection_name=collection_name,
                products=normalized_products,
                embeddings=product_embeddings
            )
            
            insert_time = time.time() - insert_start
            
            print(f"   Temps insertion: {insert_time:.2f}s")
            print()
            
            # ============================================================
            # ÉTAPE 6: RECHERCHE SÉMANTIQUE VECTORIELLE
            # ⚠️ AUDIT: Recherche sur données temporaires en RAM
            # ============================================================
            print("🔍 ÉTAPE 6/6: Recherche sémantique (Qdrant)")
            print("-" * 60)
            
            # ⚠️ IMPORTANT: Retourner TOUS les produits (pas de limite)
            search_results = self.qdrant_service.search_similar_products(
                collection_name=collection_name,
                query_embedding=query_embedding,
                limit=len(normalized_products),  # Tous les produits
                score_threshold=0.0
            )
            
            print()
            
            # ============================================================
            # NETTOYAGE: SUPPRESSION COLLECTION TEMPORAIRE
            # ⚠️ AUDIT: Nettoyage explicite des données éphémères
            # ============================================================
            print("🗑️ NETTOYAGE: Suppression collection temporaire")
            print("-" * 60)
            
            self.qdrant_service.delete_temporary_collection(collection_name)
            print()
            
            # ============================================================
            # RÉSULTATS
            # ============================================================
            pipeline_time = time.time() - pipeline_start
            
            print("=" * 60)
            print("✅ PIPELINE TERMINÉ")
            print("=" * 60)
            print(f"⏱️ Temps total: {pipeline_time:.2f}s")
            print(f"📊 Produits scrapés: {len(products)}")
            print(f"🎯 Résultats retournés: {len(search_results)}")
            print(f"⚠️ AUDIT: Toutes les données temporaires ont été supprimées")
            print("=" * 60)
            print()
            
            return {
                "success": True,
                "query": user_query,
                "products": [
                    {
                        **result["product"],
                        "score": result["score"],
                        "metadata": {
                            **(result["product"].get("metadata", {})),
                            "source": result["product"].get("source", "unknown")
                        }
                    } for result in search_results
                ],  # Frontend expects 'products'
                "results": search_results,  # Keep original for compatibility
                "total_found": len(products),
                "total_returned": len(search_results),
                "pipeline_time_seconds": pipeline_time,
                "summary": f"Found {len(search_results)} products matching '{user_query}' from {len(products)} scraped items",
                "intent": {
                    "product_type": user_query,
                    "search_terms": user_query.split(),
                    "platforms_used": [
                        platform for platform, enabled in [
                            ("Amazon", use_amazon),
                            ("Alibaba", use_alibaba), 
                            ("Walmart", use_walmart),
                            ("Cdiscount", use_cdiscount)
                        ] if enabled
                    ]
                },
                "metrics": {
                    "scraping_time": scraping_time,
                    "embedding_time": embedding_time,
                    "insert_time": insert_time,
                    "total_time": pipeline_time
                },
                "audit_info": {
                    "qdrant_mode": "memory",
                    "collection_deleted": True,
                    "data_persisted": False,
                    "temporary_collection_name": collection_name
                }
            }
            
        except Exception as e:
            print(f"❌ ERREUR dans le pipeline: {e}")
            
            # Nettoyage en cas d'erreur
            try:
                self.qdrant_service.delete_temporary_collection(collection_name)
                print(f"✅ Collection temporaire nettoyée après erreur")
            except:
                pass
            
            raise e
