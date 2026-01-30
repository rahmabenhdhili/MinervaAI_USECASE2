"""
Service Marketing - Génération de stratégies marketing avec Groq LLM
"""

from groq import Groq
from config import get_settings
from typing import Dict, Optional


class MarketingService:
    """Service pour générer des stratégies marketing pour les produits"""
    
    def __init__(self, debug: bool = False):
        settings = get_settings()
        
        # Initialize Groq client with error handling for compatibility issues
        try:
            self.client = Groq(api_key=settings.groq_api_key)
        except TypeError as e:
            if "proxies" in str(e):
                # Handle compatibility issue with httpx and proxies
                import httpx
                # Create a custom httpx client without proxies
                http_client = httpx.Client()
                self.client = Groq(api_key=settings.groq_api_key, http_client=http_client)
            else:
                raise e
        
        self.model = settings.groq_model
        self.debug = debug
        
        if debug:
            print(f"✅ Marketing Service initialisé")
            print(f"   🤖 Modèle: {self.model}")
    
    def generate_marketing_strategy(
        self, 
        product_name: str, 
        product_description: str
    ) -> Dict[str, str]:
        """
        Génère une stratégie marketing pour un produit
        
        Args:
            product_name: Nom du produit
            product_description: Description du produit
        
        Returns:
            Dict avec la stratégie marketing structurée
        """
        
        if self.debug:
            print(f"\n📊 Génération stratégie marketing pour: {product_name[:50]}...")
        
        # Prompt marketing
        prompt = f"""Tu es un expert en marketing e-commerce.

À partir du NOM et de la DESCRIPTION du produit ci-dessous,
génère une stratégie marketing simple et claire pour aider
l'utilisateur à mieux vendre ce produit sur son site e-commerce.

Produit :
Nom : {product_name}
Description : {product_description}

Ta réponse doit contenir :
1. Une courte analyse du produit (à quoi il sert, pour qui)
2. Le positionnement marketing du produit
3. 4 à 6 étapes concrètes pour le promouvoir
4. Des idées marketing simples (offres, messages, promotions)
5. Des conseils pour améliorer la visibilité et les ventes

Contraintes :
- Ne publie rien automatiquement
- Ne modifie pas le produit
- Donne uniquement des conseils
- Langage simple, clair et actionnable
- Réponse structurée avec des titres

Format de réponse attendu:

## 1. ANALYSE DU PRODUIT
[Analyse courte]

## 2. POSITIONNEMENT MARKETING
[Positionnement]

## 3. ÉTAPES DE PROMOTION
1. [Étape 1]
2. [Étape 2]
3. [Étape 3]
4. [Étape 4]

## 4. IDÉES MARKETING
- [Idée 1]
- [Idée 2]
- [Idée 3]

## 5. CONSEILS VISIBILITÉ
- [Conseil 1]
- [Conseil 2]
- [Conseil 3]
"""
        
        try:
            # Appel à Groq LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un expert en marketing e-commerce. Tu donnes des conseils pratiques et actionnables."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            strategy = response.choices[0].message.content
            
            if self.debug:
                print(f"✅ Stratégie générée ({len(strategy)} caractères)")
            
            return {
                "product_name": product_name,
                "product_description": product_description,
                "strategy": strategy,
                "success": True
            }
            
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur génération stratégie: {e}")
            
            return {
                "product_name": product_name,
                "product_description": product_description,
                "strategy": "Erreur lors de la génération de la stratégie marketing.",
                "success": False,
                "error": str(e)
            }
    
    def generate_bulk_strategies(
        self, 
        products: list
    ) -> list:
        """
        Génère des stratégies marketing pour plusieurs produits
        
        Args:
            products: Liste de dicts avec 'name' et 'description'
        
        Returns:
            Liste de stratégies marketing
        """
        
        if self.debug:
            print(f"\n📊 Génération de {len(products)} stratégies marketing...")
        
        strategies = []
        
        for i, product in enumerate(products, 1):
            if self.debug:
                print(f"\n[{i}/{len(products)}] {product.get('name', 'Produit')[:40]}...")
            
            strategy = self.generate_marketing_strategy(
                product_name=product.get('name', 'Produit'),
                product_description=product.get('description', '')
            )
            
            strategies.append(strategy)
        
        if self.debug:
            print(f"\n✅ {len(strategies)} stratégies générées")
        
        return strategies
