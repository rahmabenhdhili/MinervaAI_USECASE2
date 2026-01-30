import json
import logging
import re
from typing import List, Dict, Any, Set
from groq import Groq
from .models_usershop import Product, ProductRecommendation, RecommendationResponse
from .config_usershop import settings

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
            # Nettoyer et extraire le nombre (support €, TND, $, etc.)
            price_clean = str(price_str).replace('€', '').replace('TND', '').replace('$', '').replace(',', '.').strip()
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
        """Filtre les produits par fourchette de prix numérique et élimine prix = 0"""
        filtered = []
        
        for product in products:
            price_value = self.extract_price_value(product.get('price', '0'))
            
            # Ajouter le prix numérique
            product['price_numeric'] = price_value
            
            # Éliminer les produits à prix 0 ou invalide
            if price_value <= 0:
                continue
            
            # Appliquer les filtres min/max
            passes_filter = True
            
            if min_price is not None and price_value < min_price:
                passes_filter = False
            
            if max_price is not None and price_value > max_price:
                passes_filter = False
            
            if passes_filter:
                filtered.append(product)
        
        logger.info(f"💰 Filtrage prix: {len(products)} → {len(filtered)} produits (min={min_price}, max={max_price}, prix>0)")
        return filtered
    
    def calculate_relevance_score(
        self, 
        product: Dict[str, Any], 
        search_criteria: Dict[str, Any]
    ) -> float:
        """
        Calcule un score de pertinence ultra-précis avec barème optimisé
        Échelle: 0-100 points
        """
        score = 0.0
        
        # Préparer les textes
        product_name = product.get('name', '').lower()
        product_desc = product.get('description', '').lower()
        product_category = product.get('category', '').lower()
        product_brand = product.get('brand', '').lower()
        product_text = f"{product_name} {product_desc} {product_category} {product_brand}"
        
        # 1. SIMILARITÉ VECTORIELLE (Qdrant) - Base fondamentale (0-30 points)
        if product.get('score'):
            vector_score = product['score'] * 30.0  # Normaliser sur 30 points max
            score += vector_score
        
        # 2. CORRESPONDANCE NOM (0-25 points)
        if search_criteria.get('name'):
            search_name = search_criteria['name'].lower()
            name_terms = [t for t in search_name.split() if len(t) > 2]
            
            if name_terms:
                # Bonus si TOUS les termes sont présents dans le nom
                all_terms_in_name = all(term in product_name for term in name_terms)
                if all_terms_in_name:
                    score += 20.0  # Correspondance parfaite
                else:
                    # Score proportionnel au nombre de termes trouvés
                    terms_found = sum(1 for term in name_terms if term in product_name)
                    score += (terms_found / len(name_terms)) * 15.0
                    
                    # Bonus partiel si termes dans le texte complet
                    terms_in_text = sum(1 for term in name_terms if term in product_text and term not in product_name)
                    score += (terms_in_text / len(name_terms)) * 5.0
        
        # 3. CORRESPONDANCE CATÉGORIE (0-20 points)
        if search_criteria.get('category'):
            search_category = search_criteria['category'].lower()
            
            # Correspondance exacte
            if search_category == product_category:
                score += 20.0
            # Correspondance partielle (inclusion)
            elif search_category in product_category or product_category in search_category:
                score += 15.0
            else:
                # Score basé sur mots-clés communs
                search_cat_words = set(search_category.split())
                product_cat_words = set(product_category.split())
                common_words = search_cat_words & product_cat_words
                
                if search_cat_words:
                    category_match_ratio = len(common_words) / len(search_cat_words)
                    score += category_match_ratio * 10.0
        
        # 4. CORRESPONDANCE DESCRIPTION (0-15 points)
        if search_criteria.get('description'):
            search_desc = search_criteria['description'].lower()
            desc_terms = [t for t in search_desc.split() if len(t) > 3]
            
            if desc_terms:
                # Termes dans description produit
                terms_in_desc = sum(1 for term in desc_terms if term in product_desc)
                # Termes dans nom produit (bonus)
                terms_in_name = sum(1 for term in desc_terms if term in product_name)
                
                desc_score = (terms_in_desc / len(desc_terms)) * 10.0
                name_bonus = (terms_in_name / len(desc_terms)) * 5.0
                
                score += desc_score + name_bonus
        
        # 5. PERTINENCE PRIX (0-10 points)
        min_price = search_criteria.get('min_price')
        max_price = search_criteria.get('max_price')
        
        if min_price is not None or max_price is not None:
            price_value = product.get('price_numeric', 0)
            
            # Vérifier si dans la fourchette
            in_range = True
            if min_price is not None and price_value < min_price:
                in_range = False
            if max_price is not None and price_value > max_price:
                in_range = False
            
            if in_range:
                score += 5.0  # Bonus base pour être dans la fourchette
                
                # Bonus supplémentaire si proche du milieu de la fourchette
                if min_price is not None and max_price is not None:
                    mid_price = (min_price + max_price) / 2
                    distance = abs(price_value - mid_price)
                    range_size = max_price - min_price
                    
                    if range_size > 0:
                        # Plus proche du milieu = meilleur score
                        proximity_ratio = 1 - (distance / range_size)
                        score += proximity_ratio * 5.0
        
        # Score final normalisé sur 100
        return min(score, 100.0)
    
    def remove_duplicates_and_similar(
        self, 
        products: List[Dict[str, Any]], 
        target_product: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Supprime les doublons exacts mais garde les produits similaires (seuil 95%)"""
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
            
            # Vérifier les noms trop similaires (seuil augmenté à 95% pour garder plus de produits)
            is_too_similar = False
            for seen_name in seen_names:
                # Si 95% des mots sont identiques, considérer comme doublon
                name_words = set(name.split())
                seen_words = set(seen_name.split())
                
                if name_words and seen_words:
                    common = name_words & seen_words
                    similarity = len(common) / max(len(name_words), len(seen_words))
                    
                    if similarity > 0.95:  # Augmenté de 0.8 à 0.95
                        is_too_similar = True
                        break
            
            if not is_too_similar:
                unique_products.append(product)
                seen_names.add(name)
                seen_combinations.add(signature)
        
        logger.info(f"🔄 Suppression doublons: {len(products)} → {len(unique_products)} produits uniques (seuil 95%)")
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
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Sélection ultra-précise des meilleurs produits
        Phase sélective: garde les 20 meilleurs scores
        Supporte tri par prix et score
        """
        logger.info(f"🎯 Sélection des meilleurs produits parmi {len(products)} candidats")
        
        # Étape 1: Filtrer par prix (élimine aussi prix = 0)
        filtered = self.filter_by_price_range(
            products, 
            search_criteria.get('min_price'), 
            search_criteria.get('max_price')
        )
        
        if not filtered:
            logger.warning("⚠️ Aucun produit après filtrage prix")
            return []
        
        # Étape 2: Calculer les scores de pertinence
        scored_products = []
        for product in filtered:
            relevance_score = self.calculate_relevance_score(product, search_criteria)
            product_copy = product.copy()
            product_copy['relevance_score'] = relevance_score
            scored_products.append(product_copy)
        
        # Étape 3: Phase sélective - Garder les 20 meilleurs scores
        scored_products.sort(key=lambda x: x['relevance_score'], reverse=True)
        top_20 = scored_products[:20]
        logger.info(f"⭐ Phase sélective: {len(scored_products)} → Top 20 meilleurs scores")
        
        # Étape 4: Trier selon le critère demandé
        sort_by = search_criteria.get('sort_by', 'relevance')
        
        if sort_by == 'price_asc':
            # Tri par prix croissant
            top_20.sort(key=lambda x: x.get('price_numeric', 999999))
            logger.info(f"📊 Tri par prix croissant")
        elif sort_by == 'price_desc':
            # Tri par prix décroissant
            top_20.sort(key=lambda x: x.get('price_numeric', 0), reverse=True)
            logger.info(f"📊 Tri par prix décroissant")
        else:
            # Déjà trié par pertinence
            logger.info(f"📊 Tri par pertinence (score)")
        
        # Étape 5: Supprimer les doublons
        unique_products = self.remove_duplicates_and_similar(top_20)
        
        # Étape 6: Appliquer la limite si spécifiée
        if limit is not None:
            # Assurer la diversité seulement si limite spécifiée
            diverse_products = self.ensure_diversity(unique_products, limit)
        else:
            # Retourner tous les produits uniques
            diverse_products = unique_products
        
        # Log des meilleurs résultats
        if diverse_products:
            top_count = min(5, len(diverse_products))
            logger.info(f"📊 Top {top_count} résultats finaux:")
            for i, p in enumerate(diverse_products[:top_count], 1):
                price = p.get('price_numeric', 0)
                score = p.get('relevance_score', 0)
                logger.info(f"   {i}. {p.get('name')[:50]} - Prix: {price:.2f} TND - Score: {score:.1f}/100")
        
        logger.info(f"✨ {len(diverse_products)} produits sélectionnés après filtrage complet")
        
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
        search_criteria: Dict[str, Any],
        total_found: int,
        total_after_filter: int
    ) -> RecommendationResponse:
        """Génère des recommandations ultra-précises"""
        try:
            logger.info(f"🎨 Génération des recommandations pour: {target_product.get('name')}")
            
            # Générer la description du produit principal
            product_description = await self.generate_product_description(target_product)
            
            # Supprimer le produit cible et les doublons
            candidates = self.remove_duplicates_and_similar(similar_products, target_product)
            
            # Créer les objets de recommandation avec scores
            recommendations = []
            for product in candidates:
                recommendation = ProductRecommendation(
                    id=product.get('id'),  # Inclure l'ID pour la comparaison
                    name=product.get('name', ''),
                    category=product.get('category', ''),
                    brand=product.get('brand', ''),
                    price=product.get('price', ''),
                    img=product.get('img', ''),
                    url=product.get('url', ''),
                    score=round(product.get('relevance_score', 0), 2),
                    price_numeric=product.get('price_numeric', 0)
                )
                recommendations.append(recommendation)
            
            logger.info(f"✅ {len(recommendations)} recommandations uniques générées")
            
            return RecommendationResponse(
                product_description=product_description,
                recommendations=recommendations,
                total_found=total_found,
                total_after_filter=total_after_filter
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur génération recommandations: {e}")
            return RecommendationResponse(
                product_description="Description non disponible",
                recommendations=[],
                total_found=0,
                total_after_filter=0
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
    
    async def compare_products(
        self,
        product_1: Dict[str, Any],
        product_2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare deux produits avec focus sur guide monétaire et technique"""
        try:
            logger.info(f"🔄 Comparaison: {product_1.get('name')} vs {product_2.get('name')}")
            
            # Extraire les prix
            price_1 = self.extract_price_value(product_1.get('price', '0'))
            price_2 = self.extract_price_value(product_2.get('price', '0'))
            
            # Préparer les informations des produits
            p1_info = f"""
Produit 1: {product_1.get('name')}
Marque: {product_1.get('brand')}
Catégorie: {product_1.get('category')}
Prix: {product_1.get('price')} ({price_1} TND)
Description: {product_1.get('description', '')[:400]}
"""
            
            p2_info = f"""
Produit 2: {product_2.get('name')}
Marque: {product_2.get('brand')}
Catégorie: {product_2.get('category')}
Prix: {product_2.get('price')} ({price_2} TND)
Description: {product_2.get('description', '')[:400]}
"""
            
            # Prompt optimisé avec focus monétaire
            prompt = f"""Tu es un expert en analyse produits. Compare ces deux produits avec un FOCUS MAJEUR sur l'aspect monétaire. Les prix sont en Dinars Tunisiens (TND).

{p1_info}

{p2_info}

Fournis une analyse au format JSON suivant:

{{
  "product_1_analysis": {{
    "product_name": "nom complet",
    "price": "{product_1.get('price')}",
    "explanation": "description technique claire (2-3 phrases)",
    "advantages": ["avantage 1", "avantage 2", "avantage 3"],
    "disadvantages": ["inconvénient 1", "inconvénient 2"],
    "best_for": "type d'utilisateur idéal (1 phrase)"
  }},
  "product_2_analysis": {{
    "product_name": "nom complet",
    "price": "{product_2.get('price')}",
    "explanation": "description technique claire (2-3 phrases)",
    "advantages": ["avantage 1", "avantage 2", "avantage 3"],
    "disadvantages": ["inconvénient 1", "inconvénient 2"],
    "best_for": "type d'utilisateur idéal (1 phrase)"
  }},
  "monetary_guide": {{
    "price_difference": "différence de prix exacte et pourcentage (ex: 20 TND soit 25% plus cher)",
    "value_analysis": "analyse détaillée de la valeur pour l'argent - quel produit offre le meilleur rapport qualité/prix et pourquoi (3-4 phrases)",
    "budget_recommendation": "recommandation claire selon le budget - petit budget vs budget confortable (2-3 phrases)",
    "long_term_cost": "analyse du coût à long terme - durabilité, entretien, remplacement (2-3 phrases)"
  }},
  "technical_guide": {{
    "quality_comparison": "comparaison de la qualité des matériaux et fabrication (2-3 phrases)",
    "features_comparison": "comparaison des caractéristiques et fonctionnalités (2-3 phrases)",
    "durability_analysis": "analyse de la durabilité et longévité (2 phrases)",
    "performance_rating": "évaluation des performances - lequel performe mieux et dans quels domaines (2 phrases)"
  }},
  "final_recommendation": "Produit 1 ou Produit 2",
  "recommendation_reason": "raison principale du choix en 2-3 phrases - DOIT mentionner l'aspect prix/valeur"
}}

RÈGLES CRITIQUES:
- Le guide monétaire est PRIORITAIRE
- Analyse détaillée de la valeur pour l'argent
- Comparaison prix/qualité explicite
- Recommandation selon budget
- Ton professionnel et objectif
- JSON valide uniquement
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un expert en analyse produits avec focus sur l'aspect monétaire. Tu réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            comparison_text = response.choices[0].message.content.strip()
            
            # Parser le JSON
            if comparison_text.startswith("```json"):
                comparison_text = comparison_text[7:]
            if comparison_text.startswith("```"):
                comparison_text = comparison_text[3:]
            if comparison_text.endswith("```"):
                comparison_text = comparison_text[:-3]
            
            comparison_data = json.loads(comparison_text.strip())
            
            logger.info(f"✅ Comparaison générée avec focus monétaire")
            return comparison_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur parsing JSON: {e}")
            return self._generate_fallback_comparison(product_1, product_2)
        except Exception as e:
            logger.error(f"❌ Erreur comparaison: {e}")
            return self._generate_fallback_comparison(product_1, product_2)
    
    def _generate_fallback_comparison(
        self,
        product_1: Dict[str, Any],
        product_2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Génère une comparaison basique avec focus monétaire"""
        p1_price = self.extract_price_value(product_1.get('price', '0'))
        p2_price = self.extract_price_value(product_2.get('price', '0'))
        
        diff = abs(p1_price - p2_price)
        cheaper = "Produit 1" if p1_price < p2_price else "Produit 2"
        cheaper_price = min(p1_price, p2_price)
        expensive_price = max(p1_price, p2_price)
        
        percent = (diff / expensive_price * 100) if expensive_price > 0 else 0
        
        return {
            "product_1_analysis": {
                "product_name": product_1.get('name'),
                "price": product_1.get('price'),
                "explanation": f"{product_1.get('name')} de {product_1.get('brand')} dans la catégorie {product_1.get('category')}.",
                "advantages": ["Produit de qualité", "Bonne marque", "Catégorie reconnue"],
                "disadvantages": ["Informations limitées disponibles"],
                "best_for": "Utilisateurs recherchant cette catégorie de produits"
            },
            "product_2_analysis": {
                "product_name": product_2.get('name'),
                "price": product_2.get('price'),
                "explanation": f"{product_2.get('name')} de {product_2.get('brand')} dans la catégorie {product_2.get('category')}.",
                "advantages": ["Produit de qualité", "Bonne marque", "Catégorie reconnue"],
                "disadvantages": ["Informations limitées disponibles"],
                "best_for": "Utilisateurs recherchant cette catégorie de produits"
            },
            "monetary_guide": {
                "price_difference": f"{diff:.2f} TND de différence soit {percent:.1f}% plus cher",
                "value_analysis": f"Le {cheaper} à {cheaper_price:.2f} TND offre un meilleur rapport qualité-prix immédiat. La différence de {diff:.2f} TND représente {percent:.1f}% d'économie.",
                "budget_recommendation": f"Budget serré: choisir le {cheaper}. Budget confortable: les deux options sont viables selon vos préférences.",
                "long_term_cost": "Sans informations détaillées sur la durabilité, le coût à long terme est difficile à évaluer. Privilégiez la qualité pour un investissement durable."
            },
            "technical_guide": {
                "quality_comparison": "Les deux produits appartiennent à la même catégorie avec des standards de qualité similaires.",
                "features_comparison": "Caractéristiques comparables dans cette gamme de prix.",
                "durability_analysis": "Durabilité attendue similaire pour cette catégorie de produits.",
                "performance_rating": "Performances équivalentes selon les standards de la catégorie."
            },
            "final_recommendation": cheaper,
            "recommendation_reason": f"Le {cheaper} offre le meilleur rapport qualité-prix avec une économie de {diff:.2f}€ ({percent:.1f}%) tout en maintenant une qualité comparable."
        }

# Instance globale
advanced_llm_service = AdvancedLLMService()

# Instance globale
advanced_llm_service = AdvancedLLMService()
