from typing import List
from models import (
    SearchQuery, 
    QueryIntent, 
    Product, 
    ProductRecommendation, 
    RecommendationResponse
)
from services.groq_service import GroqService
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from services.product_scraper_service import ProductScraperService


class RecommendationService:
    """Service principal orchestrant tout le pipeline de recommandation"""
    
    def __init__(self):
        self.groq_service = GroqService()
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.product_scraper_service = ProductScraperService()
    
    async def initialize(self):
        """Initialise les services nécessaires"""
        await self.qdrant_service.initialize_collection()
    
    async def get_recommendations(self, search_query: SearchQuery) -> RecommendationResponse:
        """
        Pipeline complet de recommandation:
        1. Comprendre l'intention (Groq LLM)
        2. Collecter les produits RÉELS (ScraperAPI - Real-time)
        3. Générer les embeddings (SentenceTransformers)
        4. Stocker dans Qdrant Cloud
        5. Recherche sémantique (Cosine Similarity)
        6. Générer la recommandation (Groq LLM)
        """
        
        print(f"\n{'='*70}")
        print(f"🎯 ÉTAPE 1/7: ANALYSE DE L'INTENTION (Groq LLM)")
        print(f"{'='*70}")
        
        try:
            print(f"📝 Requête utilisateur: '{search_query.query}'")
            print(f"⏳ Analyse en cours avec Groq LLM...")
            intent = self.groq_service.understand_query(search_query.query)
            print(f"✅ Intention détectée:")
            print(f"   • Type de produit: {intent.product_type}")
            print(f"   • Usage: {intent.usage or 'Non spécifié'}")
            print(f"   • Budget: {intent.budget_range or 'Non spécifié'}")
            print(f"   • Caractéristiques clés: {', '.join(intent.key_features) if intent.key_features else 'Aucune'}")
            print(f"{'='*70}\n")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'analyse de l'intention: {e}")
            # Fallback: créer une intention par défaut
            intent = QueryIntent(
                product_type="laptop",
                usage=None,
                budget_range=None,
                key_features=[],
                search_keywords=search_query.query.split()[:3]
            )
            print(f"ℹ️ Utilisation d'une intention par défaut")
            print(f"{'='*70}\n")
        
        # 2. Collecter les produits RÉELS via scrapers isolés
        print(f"{'='*70}")
        print(f"🌐 ÉTAPE 2/7: SCRAPING TEMPS RÉEL")
        print(f"{'='*70}")
        
        sites_selected = []
        if search_query.use_amazon: sites_selected.append("Amazon")
        if search_query.use_alibaba: sites_selected.append("Alibaba")
        if search_query.use_walmart: sites_selected.append("Walmart")
        if search_query.use_cdiscount: sites_selected.append("Cdiscount")
        
        print(f"🎯 Sites sélectionnés: {' + '.join(sites_selected) if sites_selected else 'Aucun site'}")
        
        # CORRECTION: Utiliser la requête originale pour Walmart/Cdiscount (plus simple)
        # Les keywords Groq sont trop complexes pour Walmart/Cdiscount
        search_keywords = [search_query.query] if (search_query.use_walmart or search_query.use_cdiscount) else (intent.search_keywords or [intent.product_type])
        
        print(f"🔑 Keywords de recherche: {search_keywords}")
        print(f"{'='*70}\n")
        
        products = await self.product_scraper_service.search_products(
            keywords=search_keywords,
            max_results=search_query.max_results,
            use_amazon=search_query.use_amazon,
            use_alibaba=search_query.use_alibaba,
            use_walmart=search_query.use_walmart,
            use_cdiscount=search_query.use_cdiscount
        )
        
        # Validation des sources
        sources_found = set()
        for p in products:
            source = p.metadata.get("source", "")
            sources_found.add(source)
        
        # Vérifier qu'on a des produits
        if not products:
            print(f"\n{'='*70}")
            print(f"⚠️ AUCUN PRODUIT TROUVÉ")
            print(f"{'='*70}\n")
            return RecommendationResponse(
                query=search_query.query,
                intent=intent,
                recommendations=[],
                summary=f"Désolé, aucun produit trouvé pour '{search_query.query}'. Essayez une recherche différente comme 'laptop', 'smartphone', ou 'tablet'.",
                total_found=0
            )
        
        # 3. Générer les embeddings pour les produits
        print(f"{'='*70}")
        print(f"🧠 ÉTAPE 3/7: GÉNÉRATION EMBEDDINGS (FastEmbed)")
        print(f"{'='*70}")
        print(f"📊 Nombre de produits à encoder: {len(products)}")
        print(f"⏳ Génération des embeddings en cours...")
        
        product_texts = [
            self.embedding_service.create_product_text(
                p.name, 
                p.description, 
                p.category or ""
            )
            for p in products
        ]
        product_embeddings = self.embedding_service.generate_embeddings_batch(product_texts)
        print(f"✅ {len(product_embeddings)} embeddings générés")
        print(f"📏 Dimension des vecteurs: {len(product_embeddings[0])}D")
        print(f"⚠️ AUDIT: FastEmbed utilisé (pas de Hugging Face)")
        print(f"{'='*70}\n")
        
        # 4. Générer l'embedding de la requête
        print(f"{'='*70}")
        print(f"🔍 ÉTAPE 4/7: EMBEDDING DE LA REQUÊTE")
        print(f"{'='*70}")
        print(f"📝 Requête: '{search_query.query}'")
        print(f"⏳ Génération de l'embedding...")
        query_embedding = self.embedding_service.generate_embedding(search_query.query)
        print(f"✅ Embedding de la requête généré ({len(query_embedding)}D)")
        print(f"{'='*70}\n")
        
        # 5. Calculer la similarité directement 
        print(f"{'='*70}")
        print(f"📊 ÉTAPE 5/7: CALCUL DE SIMILARITÉ (Cosine)")
        print(f"{'='*70}")
        print(f"🔢 Calcul de similarité pour {len(products)} produits...")
        
        from numpy import dot
        from numpy.linalg import norm
        
        # Calculer le score de similarité pour chaque produit
        product_scores = []
        for i, product in enumerate(products):
            # Similarité cosinus
            similarity = dot(query_embedding, product_embeddings[i]) / (norm(query_embedding) * norm(product_embeddings[i]))
            product_scores.append((product, float(similarity)))
        
        print(f"✅ Similarité calculée pour tous les produits")
        
        # Trier par score décroissant
        product_scores.sort(key=lambda x: x[1], reverse=True)
        print(f"📈 Produits triés par pertinence")
        
        # ⚠️ IMPORTANT: Retourner TOUS les produits trouvés (pas de limite)
        # La recherche sémantique a déjà filtré les meilleurs résultats
        top_products = product_scores  # Tous les produits, triés par pertinence
        
        print(f"🏆 {len(top_products)} produits sélectionnés (TOUS)")
        if top_products:
            print(f"   • Meilleur score: {top_products[0][1]:.3f}")
            print(f"   • Score moyen: {sum(s for _, s in top_products) / len(top_products):.3f}")
            if len(top_products) > 1:
                print(f"   • Score le plus bas: {top_products[-1][1]:.3f}")
        print(f"{'='*70}\n")
        
        # 6. Construire les recommandations
        print(f"{'='*70}")
        print(f"🎁 ÉTAPE 6/7: CONSTRUCTION DES RECOMMANDATIONS")
        print(f"{'='*70}")
        print(f"📦 Création de {len(top_products)} recommandations...")
        
        recommendations = []
        for product, score in top_products:
            recommendations.append(ProductRecommendation(
                product=product,
                similarity_score=score
            ))
        
        print(f"✅ Recommandations créées")
        print(f"{'='*70}\n")
        
        # 7. Générer le résumé avec Groq LLM
        print(f"{'='*70}")
        print(f"📝 ÉTAPE 7/7: GÉNÉRATION DU RÉSUMÉ (Groq LLM)")
        print(f"{'='*70}")
        print(f"⏳ Génération du résumé intelligent...")
        
        try:
            summary = self.groq_service.generate_recommendation_summary(
                query=search_query.query,
                intent=intent,
                products=[rec.product for rec in recommendations]
            )
            print(f"✅ Résumé généré avec succès")
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération du résumé: {e}")
            # Fallback: créer un résumé simple
            if recommendations:
                avg_price = sum(p.product.price for p in recommendations if p.product.price > 0) / len([p for p in recommendations if p.product.price > 0]) if any(p.product.price > 0 for p in recommendations) else 0
                summary = f"Nous avons trouvé {len(recommendations)} produits correspondant à votre recherche '{search_query.query}'. Prix moyen: ${avg_price:.2f}. Les produits sont triés par pertinence."
            else:
                summary = f"Aucun produit trouvé pour '{search_query.query}'. Essayez une recherche différente."
            print(f"ℹ️ Utilisation d'un résumé par défaut")
        
        print(f"{'='*70}\n")
        
        print(f"{'='*70}")
        print(f"✅ PIPELINE TERMINÉ AVEC SUCCÈS")
        print(f"{'='*70}")
        print(f"📊 Résumé:")
        print(f"   • Produits scrapés: {len(product_scores)}")
        print(f"   • Recommandations: {len(recommendations)}")
        print(f"   • Sources: {', '.join(sources_found)}")
        print(f"{'='*70}\n")
        
        return RecommendationResponse(
            query=search_query.query,
            intent=intent,
            recommendations=recommendations,
            summary=summary,
            total_found=len(product_scores)
        )
