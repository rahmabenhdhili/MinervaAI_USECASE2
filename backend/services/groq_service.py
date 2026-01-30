import json
from groq import Groq
from typing import List
from models import QueryIntent, Product
from config import get_settings


class GroqService:
    """Service pour interagir avec Groq API"""
    
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
    
    def understand_query(self, query: str) -> QueryIntent:
        """Analyse l'intention de la requête utilisateur avec détection améliorée des catégories"""
        
        try:
            prompt = f"""Tu es un expert en analyse de requêtes e-commerce. Analyse cette requête et extrais les informations structurées.

Requête: "{query}"

IMPORTANT - Détection de catégorie:
- Si la requête contient "cat" ou "cats" SEUL (sans autre mot), c'est probablement "pet supplies" ou "cat products"
- Si c'est "camera" ou "cam", c'est "camera"
- Fais attention aux abréviations et mots courts

Catégories principales:
- Electronics: laptop, phone, tablet, camera, headphones, speaker, monitor, keyboard, mouse
- Pet Supplies: cat, dog, pet, animal supplies
- Clothing: shirt, pants, dress, shoes, jacket
- Home: furniture, decor, kitchen, bedding
- Sports: fitness, outdoor, sports equipment
- Beauty: makeup, skincare, cosmetics
- Toys: games, toys, kids products

Retourne un JSON avec:
- product_type: type de produit principal (laptop, phone, camera, cat supplies, etc.)
- usage: usage prévu si mentionné (gaming, work, travel, pet care, etc.)
- budget_range: fourchette de prix si mentionnée (ex: "500-1000")
- key_features: liste des caractéristiques importantes mentionnées
- search_keywords: 3-5 mots-clés optimisés pour la recherche Amazon/Alibaba

EXEMPLES:

1. "cats" ou "cat"
   {{"product_type": "cat supplies", "usage": "pet care", "budget_range": null, "key_features": ["cat", "pet"], "search_keywords": ["cat supplies", "cat products", "pet supplies"]}}

2. "camera"
   {{"product_type": "camera", "usage": null, "budget_range": null, "key_features": ["camera"], "search_keywords": ["digital camera", "camera", "photography"]}}

3. "laptop gaming"
   {{"product_type": "laptop", "usage": "gaming", "budget_range": null, "key_features": ["gaming"], "search_keywords": ["gaming laptop computer", "high performance", "gaming"]}}

4. "dog food"
   {{"product_type": "dog supplies", "usage": "pet care", "budget_range": null, "key_features": ["dog", "food"], "search_keywords": ["dog food", "pet food", "dog supplies"]}}

5. "wireless headphones"
   {{"product_type": "headphones", "usage": null, "budget_range": null, "key_features": ["wireless"], "search_keywords": ["wireless headphones", "bluetooth headphones", "headphones"]}}

Réponds UNIQUEMENT avec le JSON, sans texte additionnel."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Abaissé de 0.3 à 0.2 pour plus de précision
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Nettoyer le JSON si nécessaire
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            if content.startswith("```"):
                content = content.replace("```", "").strip()
            
            intent_data = json.loads(content)
            
            # Post-traitement: Vérifier si "cat" est mal interprété
            query_lower = query.lower().strip()
            if query_lower in ["cat", "cats", "chat", "chats"] and "camera" in intent_data.get("product_type", "").lower():
                # Correction: C'est probablement des produits pour chats
                intent_data["product_type"] = "cat supplies"
                intent_data["usage"] = "pet care"
                intent_data["key_features"] = ["cat", "pet"]
                intent_data["search_keywords"] = ["cat supplies", "cat products", "pet supplies"]
            
            return QueryIntent(**intent_data)
            
        except Exception as e:
            print(f"❌ Erreur Groq understand_query: {e}")
            raise
    
    def generate_recommendation_summary(
        self, 
        query: str, 
        intent: QueryIntent, 
        products: List[Product]
    ) -> str:
        """Génère un résumé intelligent et détaillé des recommandations"""
        
        try:
            if not products:
                return f"Aucun produit trouvé pour '{query}'. Essayez une recherche différente comme 'laptop', 'smartphone', ou 'headphones'."
            
            # Préparer les infos produits
            products_info = []
            for i, p in enumerate(products[:5], 1):
                price_str = f"${p.price:.2f}" if p.price > 0 else "Prix non disponible"
                rating_str = f"⭐ {p.rating}/5" if p.rating else "Pas de note"
                products_info.append(f"{i}. {p.name[:80]} - {price_str} {rating_str}")
            
            products_text = "\n".join(products_info)
            
            # Calculer les stats
            avg_price = sum(p.price for p in products if p.price > 0) / len([p for p in products if p.price > 0]) if any(p.price > 0 for p in products) else 0
            min_price = min((p.price for p in products if p.price > 0), default=0)
            max_price = max((p.price for p in products if p.price > 0), default=0)
            
            prompt = f"""Tu es un expert shopping assistant. Génère une recommandation professionnelle et détaillée.

Requête utilisateur: "{query}"
Type de produit: {intent.product_type}
Usage: {intent.usage or 'Non spécifié'}
Budget: {intent.budget_range or 'Non spécifié'}
Caractéristiques recherchées: {', '.join(intent.key_features) if intent.key_features else 'Non spécifié'}

Top 5 produits trouvés:
{products_text}

Statistiques:
- Prix moyen: ${avg_price:.2f}
- Fourchette: ${min_price:.2f} - ${max_price:.2f}
- Total trouvés: {len(products)} produits

Génère une recommandation en 3-4 phrases qui:
1. Résume les produits trouvés et leur pertinence
2. Mentionne les points forts (prix, qualité, marques)
3. Compare les options (budget vs premium)
4. Donne un conseil d'achat concret

Sois professionnel, précis et utile. Utilise les vrais prix et données."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Erreur Groq generate_recommendation_summary: {e}")
            # Fallback simple
            if products:
                avg_price = sum(p.price for p in products if p.price > 0) / len([p for p in products if p.price > 0]) if any(p.price > 0 for p in products) else 0
                return f"J'ai trouvé {len(products)} produits correspondant à '{query}'. Prix moyen: ${avg_price:.2f}. Les produits sont triés par pertinence pour vous aider à choisir."
            return f"Produits trouvés pour '{query}'."
