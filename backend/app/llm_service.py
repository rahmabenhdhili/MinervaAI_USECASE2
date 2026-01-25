import json
import logging
import re
from typing import List, Dict, Any
from groq import Groq
from .models import Product, ProductRecommendation, RecommendationResponse
from .config import settings

logger = logging.getLogger(__name__)

class GroqLLMService:
    """Service pour la génération de descriptions et recommandations avec Groq"""
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY doit être configuré")
        
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        logger.info(f"Service Groq initialisé avec le modèle: {self.model}")
    
    def extract_price_value(self, price_str: str) -> float:
        """Extrait la valeur numérique d'un prix"""
        try:
            # Extraire les nombres du prix
            numbers = re.findall(r'\d+\.?\d*', str(price_str))
            if numbers:
                return float(numbers[0])
            return 0.0
        except:
            return 0.0
    
    def filter_by_price(self, products: List[Dict[str, Any]], price_query: str) -> List[Dict[str, Any]]:
        """Filtre les produits par prix selon la requête"""
        if not price_query:
            return products
        
        price_query_lower = price_query.lower()
        filtered = []
        
        for product in products:
            price_value = self.extract_price_value(product.get('price', '0'))
            
            # Moins de X
            if 'moins de' in price_query_lower or 'less than' in price_query_lower:
                numbers = re.findall(r'\d+', price_query)
                if numbers:
                    max_price = float(numbers[0])
                    if price_value <= max_price:
                        filtered.append(product)
            
            # Plus de X
            elif 'plus de' in price_query_lower or 'more than' in price_query_lower:
                numbers = re.findall(r'\d+', price_query)
                if numbers:
                    min_price = float(numbers[0])
                    if price_value >= min_price:
                        filtered.append(product)
            
            # Entre X et Y
            elif 'entre' in price_query_lower or 'between' in price_query_lower:
                numbers = re.findall(r'\d+', price_query)
                if len(numbers) >= 2:
                    min_price = float(numbers[0])
                    max_price = float(numbers[1])
                    if min_price <= price_value <= max_price:
                        filtered.append(product)
            
            # Autour de X
            elif 'autour' in price_query_lower or 'around' in price_query_lower:
                numbers = re.findall(r'\d+', price_query)
                if numbers:
                    target_price = float(numbers[0])
                    margin = target_price * 0.2  # 20% de marge
                    if target_price - margin <= price_value <= target_price + margin:
                        filtered.append(product)
            
            else:
                # Si pas de filtre spécifique, garder tous
                filtered.append(product)
        
        return filtered if filtered else products
    
    def score_product_relevance(
        self, 
        product: Dict[str, Any], 
        search_criteria: Dict[str, Any]
    ) -> float:
        """Score la pertinence d'un produit par rapport aux critères de recherche"""
        score = 0.0
        
        # Préparer les textes pour comparaison
        product_text = f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')} {product.get('brand', '')}".lower()
        
        # Score basé sur le nom
        if search_criteria.get('name'):
            name_terms = search_criteria['name'].lower().split()
            for term in name_terms:
                if term in product_text:
                    score += 2.0  # Poids fort pour le nom
        
        # Score basé sur la catégorie
        if search_criteria.get('category'):
            category_lower = search_criteria['category'].lower()
            product_category = product.get('category', '').lower()
            if category_lower in product_category or product_category in category_lower:
                score += 3.0  # Poids très fort pour la catégorie exacte
        
        # Score basé sur la description
        if search_criteria.get('description'):
            desc_terms = search_criteria['description'].lower().split()
            for term in desc_terms:
                if len(term) > 3 and term in product_text:  # Ignorer les mots trop courts
                    score += 1.0
        
        # Score basé sur le prix (si le produit correspond au filtre)
        if search_criteria.get('price'):
            filtered = self.filter_by_price([product], search_criteria['price'])
            if filtered:
                score += 1.5
        
        # Bonus pour le score de similarité vectorielle
        if product.get('score'):
            score += product['score'] * 5.0  # Multiplier le score Qdrant
        
        return score
    
    def select_best_products(
        self, 
        products: List[Dict[str, Any]], 
        search_criteria: Dict[str, Any],
        limit: int = 7
    ) -> List[Dict[str, Any]]:
        """Sélectionne les meilleurs produits selon les critères"""
        
        # Filtrer par prix d'abord
        if search_criteria.get('price'):
            products = self.filter_by_price(products, search_criteria['price'])
        
        # Scorer chaque produit
        scored_products = []
        for product in products:
            relevance_score = self.score_product_relevance(product, search_criteria)
            product_copy = product.copy()
            product_copy['relevance_score'] = relevance_score
            scored_products.append(product_copy)
        
        # Trier par score de pertinence
        scored_products.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Retourner les meilleurs
        return scored_products[:limit]
    
    async def generate_product_description(self, product: Dict[str, Any]) -> str:
        """Génère une description enrichie pour un produit avec Groq"""
        try:
            name = product.get('name', '')
            category = product.get('category', '')
            brand = product.get('brand', '')
            price = product.get('price', '')
            base_description = product.get('description', '')
            
            # Limiter la description de base pour le prompt
            base_description_short = ' '.join(base_description.split()[:50])
            
            prompt = f"""
            Génère une description enrichie et attrayante pour ce produit en français (maximum 120 mots) :
            
            Nom: {name}
            Marque: {brand}
            Catégorie: {category}
            Prix: {price}
            Description: {base_description_short}
            
            La description doit être:
            - Engageante et professionnelle
            - Mettre en valeur les points forts du produit
            - Mentionner le rapport qualité-prix
            - Adaptée à la catégorie du produit
            - Maximum 120 mots
            
            Réponds uniquement avec la description, sans introduction ni conclusion.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un expert en marketing produit qui crée des descriptions attrayantes et professionnelles en français."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            
            description = response.choices[0].message.content.strip()
            
            # Limiter à 120 mots
            words = description.split()
            if len(words) > 120:
                description = ' '.join(words[:120]) + '...'
            
            return description
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de description avec Groq: {e}")
            # Fallback vers une description simple
            return f"{name} de {brand} - {base_description[:200]}... Un excellent choix dans la catégorie {category} au prix de {price}."
    
    async def generate_recommendations(
        self, 
        target_product: Dict[str, Any], 
        similar_products: List[Dict[str, Any]],
        search_criteria: Dict[str, Any]
    ) -> RecommendationResponse:
        """Génère des recommandations basées sur un produit et des produits similaires"""
        try:
            # Générer la description enrichie du produit cible
            product_description = await self.generate_product_description(target_product)
            
            # Sélectionner les 6-7 meilleurs produits (exclure le produit cible)
            candidates = [p for p in similar_products if p.get('id') != target_product.get('id')]
            best_products = self.select_best_products(candidates, search_criteria, limit=7)
            
            # Créer les recommandations
            recommendations = []
            for product in best_products[:6]:  # Limiter à 6 recommandations
                recommendation = ProductRecommendation(
                    name=product.get('name', ''),
                    category=product.get('category', ''),
                    brand=product.get('brand', ''),
                    price=product.get('price', ''),
                    img=product.get('img', ''),
                    url=product.get('url', '')
                )
                recommendations.append(recommendation)
            
            logger.info(f"✅ Généré {len(recommendations)} recommandations de qualité")
            
            return RecommendationResponse(
                product_description=product_description,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de recommandations: {e}")
            return RecommendationResponse(
                product_description="Description non disponible",
                recommendations=[]
            )
    
    def create_search_query(self, request_data: Dict[str, Any]) -> str:
        """Crée une requête de recherche à partir des critères"""
        query_parts = []
        
        if request_data.get('name'):
            query_parts.append(request_data['name'])
        if request_data.get('description'):
            query_parts.append(request_data['description'])
        if request_data.get('category'):
            query_parts.append(request_data['category'])
        # Ne pas inclure le prix dans la requête vectorielle
        
        return ' '.join(query_parts) if query_parts else "produit"

# Instance globale
llm_service = GroqLLMService()