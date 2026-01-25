import json
import logging
import re
from typing import List, Dict, Any, Set
from groq import Groq
from .models import Product, ProductRecommendation, RecommendationResponse
from .config import settings

logger = logging.getLogger(__name__)

class AdvancedLLMService:
    """Service avancé pour recommandations ultra-précises"""
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY doit être configuré")
        
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        logger.info(f"🚀 Service LLM Avancé initialisé avec {self.model}")
    
    def extract_price_value(self, price_str: str) -> float:
        """Extrait la valeur numérique d'un prix avec précision"""
        try:
            # Nettoyer et extraire le nombre
            price_clean = str(price_str).replace('€', '').replace(',', '.').strip()
            numbers = re.findall(r'\d+\.?\d*', price_clean)
            if numbers:
                return float(numbers[0])
            return 0.0
        except:
            return 0.0
    
    def filter_by_price_range(
        self, 
        products: List[Dict[str, Any]], 
        min_price: float = None, 
        max_price: float = None
    ) -> List[Dict[str, Any]]:
        """Filtre les produits par fourchette de prix numérique"""
        if min_price is None and max_price is None:
            return products
        
        filtered = []
        for product in products:
            price_value = self.extract_price_value(product.get('price', '0'))
            
            # Appliquer les filtres
            if min_price is not None and price_value < min_price:
                continue
            if max_price is not None and price_value > max_price:
                continue
            
            # Ajouter le prix numérique pour tri ultérieur
            product['price_numeric'] = price_value
            filtered.append(product)
        
        logger.info(f"💰 Filtrage prix: {len(products)} → {len(filtered)} produits (min={min_price}, max={max_price})")
        return filtered
    
    def calculate_relevance_score(
        self, 
        product: Dict[str, Any], 
        search_criteria: Dict[str, Any]
    ) -> float:
        """Calcule un score de pertinence ultra-précis"""
        score = 0.0
        
        # Préparer les textes
        product_name = product.get('name', '').lower()
        product_desc = product.get('description', '').lower()
        product_category = product.get('category', '').lower()
        product_brand = product.get('brand', '').lower()
        product_text = f"{product_name} {product_desc} {product_category} {product_brand}"
        
        # 1. Score basé sur le NOM (poids très fort)
        if search_criteria.get('name'):
            search_name = search_criteria['name'].lower()
            name_terms = search_name.split()
            
            for term in name_terms:
                if len(term) > 2:  # Ignorer les mots trop courts
                    # Correspondance exacte dans le nom
                    if term in product_name:
                        score += 5.0
                    # Correspondance dans le texte complet
                    elif term in product_text:
                        score += 2.0
        
        # 2. Score basé sur la CATÉGORIE (poids très fort)
        if search_criteria.get('category'):
            search_category = search_criteria['category'].lower()
            
            # Correspondance exacte
            if search_category == product_category:
                score += 10.0
            # Correspondance partielle
            elif search_category in product_category or product_category in search_category:
                score += 7.0
            # Mots-clés de catégorie
            else:
                category_terms = search_category.split()
                for term in category_terms:
                    if len(term) > 3 and term in product_category:
                        score += 3.0
        
        # 3. Score basé sur la DESCRIPTION (poids moyen)
        if search_criteria.get('description'):
            search_desc = search_criteria['description'].lower()
            desc_terms = search_desc.split()
            
            for term in desc_terms:
                if len(term) > 3:  # Ignorer les mots courts
                    # Correspondance dans la description
                    if term in product_desc:
                        score += 2.0
                    # Correspondance dans le nom
                    elif term in product_name:
                        score += 1.5
        
        # 4. Score basé sur le PRIX (bonus si dans la fourchette)
        min_price = search_criteria.get('min_price')
        max_price = search_criteria.get('max_price')
        
        if min_price is not None or max_price is not None:
            price_value = product.get('price_numeric', 0)
            
            in_range = True
            if min_price is not None and price_value < min_price:
                in_range = False
            if max_price is not None and price_value > max_price:
                in_range = False
            
            if in_range:
                score += 3.0
                
                # Bonus si proche du milieu de la fourchette
                if min_price is not None and max_price is not None:
                    mid_price = (min_price + max_price) / 2
                    distance = abs(price_value - mid_price)
                    range_size = max_price - min_price
                    if range_size > 0:
                        proximity_score = 2.0 * (1 - distance / range_size)
                        score += max(0, proximity_score)
        
        # 5. Score de SIMILARITÉ VECTORIELLE (Qdrant)
        if product.get('score'):
            score += product['score'] * 10.0  # Poids fort pour la similarité
        
        return score
    
    def remove_duplicates_and_similar(
        self, 
        products: List[Dict[str, Any]], 
        target_product: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Supprime les doublons et produits trop similaires"""
        unique_products = []
        seen_names = set()
        seen_combinations = set()
        
        for product in products:
            # Exclure le produit cible
            if target_product and product.get('id') == target_product.get('id'):
                continue
            
            name = product.get('name', '').lower().strip()
            brand = product.get('brand', '').lower().strip()
            category = product.get('category', '').lower().strip()
            
            # Créer une signature unique
            signature = f"{name}_{brand}_{category}"
            
            # Vérifier les doublons exacts
            if signature in seen_combinations:
                continue
            
            # Vérifier les noms trop similaires
            is_too_similar = False
            for seen_name in seen_names:
                # Si 80% des mots sont identiques, considérer comme doublon
                name_words = set(name.split())
                seen_words = set(seen_name.split())
                
                if name_words and seen_words:
                    common = name_words & seen_words
                    similarity = len(common) / max(len(name_words), len(seen_words))
                    
                    if similarity > 0.8:
                        is_too_similar = True
                        break
            
            if not is_too_similar:
                unique_products.append(product)
                seen_names.add(name)
                seen_combinations.add(signature)
        
        logger.info(f"🔄 Suppression doublons: {len(products)} → {len(unique_products)} produits uniques")
        return unique_products
    
    def ensure_diversity(
        self, 
        products: List[Dict[str, Any]], 
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """Assure la diversité des recommandations"""
        if len(products) <= limit:
            return products
        
        diverse_products = []
        used_brands = set()
        used_categories = set()
        
        # Première passe : un produit par marque/catégorie
        for product in products:
            brand = product.get('brand', '').lower()
            category = product.get('category', '').lower()
            combo = f"{brand}_{category}"
            
            if combo not in used_brands:
                diverse_products.append(product)
                used_brands.add(combo)
                
                if len(diverse_products) >= limit:
                    break
        
        # Deuxième passe : compléter si nécessaire
        if len(diverse_products) < limit:
            for product in products:
                if product not in diverse_products:
                    diverse_products.append(product)
                    if len(diverse_products) >= limit:
                        break
        
        logger.info(f"🎨 Diversification: {len(products)} → {len(diverse_products)} produits variés")
        return diverse_products
    
    def select_best_products(
        self, 
        products: List[Dict[str, Any]], 
        search_criteria: Dict[str, Any],
        limit: int = 9
    ) -> List[Dict[str, Any]]:
        """
        Sélection ultra-précise des meilleurs produits
        Retourne 1 produit principal + 8 recommandations max
        """
        logger.info(f"🎯 Sélection des meilleurs produits parmi {len(products)} candidats")
        
        # Étape 1: Filtrer par prix
        filtered = self.filter_by_price_range(
            products, 
            search_criteria.get('min_price'), 
            search_criteria.get('max_price')
        )
        
        if not filtered:
            logger.warning("⚠️ Aucun produit après filtrage prix, utilisation de tous les produits")
            filtered = products
        
        # Étape 2: Calculer les scores de pertinence
        scored_products = []
        for product in filtered:
            relevance_score = self.calculate_relevance_score(product, search_criteria)
            product_copy = product.copy()
            product_copy['relevance_score'] = relevance_score
            scored_products.append(product_copy)
        
        # Étape 3: Trier par score
        scored_products.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Étape 4: Supprimer les doublons
        unique_products = self.remove_duplicates_and_similar(scored_products)
        
        # Étape 5: Assurer la diversité
        diverse_products = self.ensure_diversity(unique_products, limit)
        
        # Log des meilleurs scores
        if diverse_products:
            logger.info(f"📊 Top 3 scores:")
            for i, p in enumerate(diverse_products[:3], 1):
                logger.info(f"   {i}. {p.get('name')} - Score: {p.get('relevance_score', 0):.2f}")
        
        return diverse_products
    
    async def generate_product_description(self, product: Dict[str, Any]) -> str:
        """Génère une description enrichie et concise"""
        try:
            name = product.get('name', '')
            category = product.get('category', '')
            brand = product.get('brand', '')
            price = product.get('price', '')
            base_description = product.get('description', '')
            
            # Limiter la description de base
            base_description_short = ' '.join(base_description.split()[:40])
            
            prompt = f"""
            Génère une description marketing attrayante en français (100 mots maximum) :
            
            Produit: {name}
            Marque: {brand}
            Catégorie: {category}
            Prix: {price}
            Info: {base_description_short}
            
            Règles:
            - Concis et impactant (100 mots max)
            - Mettre en valeur les points forts
            - Mentionner le rapport qualité-prix
            - Ton professionnel et engageant
            
            Réponds uniquement avec la description.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un expert en marketing produit. Crée des descriptions concises et percutantes en français."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            description = response.choices[0].message.content.strip()
            
            # Limiter strictement à 100 mots
            words = description.split()
            if len(words) > 100:
                description = ' '.join(words[:100]) + '...'
            
            return description
            
        except Exception as e:
            logger.error(f"❌ Erreur génération description: {e}")
            return f"{name} de {brand} - {base_description[:150]}... Excellent choix dans la catégorie {category} à {price}."
    
    async def generate_recommendations(
        self, 
        target_product: Dict[str, Any], 
        similar_products: List[Dict[str, Any]],
        search_criteria: Dict[str, Any]
    ) -> RecommendationResponse:
        """Génère des recommandations ultra-précises"""
        try:
            logger.info(f"🎨 Génération des recommandations pour: {target_product.get('name')}")
            
            # Générer la description du produit principal
            product_description = await self.generate_product_description(target_product)
            
            # Supprimer le produit cible et les doublons
            candidates = self.remove_duplicates_and_similar(similar_products, target_product)
            
            # Limiter à 8 recommandations max
            best_recommendations = candidates[:8]
            
            # Créer les objets de recommandation
            recommendations = []
            for product in best_recommendations:
                recommendation = ProductRecommendation(
                    name=product.get('name', ''),
                    category=product.get('category', ''),
                    brand=product.get('brand', ''),
                    price=product.get('price', ''),
                    img=product.get('img', ''),
                    url=product.get('url', '')
                )
                recommendations.append(recommendation)
            
            logger.info(f"✅ {len(recommendations)} recommandations uniques générées")
            
            return RecommendationResponse(
                product_description=product_description,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur génération recommandations: {e}")
            return RecommendationResponse(
                product_description="Description non disponible",
                recommendations=[]
            )
    
    def create_search_query(self, request_data: Dict[str, Any]) -> str:
        """Crée une requête de recherche optimisée"""
        query_parts = []
        
        # Priorité au nom
        if request_data.get('name'):
            query_parts.append(request_data['name'])
        
        # Puis catégorie
        if request_data.get('category'):
            query_parts.append(request_data['category'])
        
        # Puis description
        if request_data.get('description'):
            query_parts.append(request_data['description'])
        
        query = ' '.join(query_parts) if query_parts else "produit"
        logger.info(f"🔍 Requête de recherche: '{query}'")
        return query

# Instance globale
advanced_llm_service = AdvancedLLMService()