from groq import Groq
import os
from typing import Dict

class GroqExplainer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        
        # Tenter d'initialiser GROQ si la clé est valide
        if api_key and api_key.strip():
            try:
                self.client = Groq(api_key=api_key)
            except Exception as e:
                print(f"⚠️ GROQ non disponible : {e}")
                print("📝 Mode explication simple activé")
    
    def explain_choice(self, best_supplier: Dict, query: str, quantity: int) -> str:
        """Génère une explication IA du choix du fournisseur"""
        
        # Si GROQ est disponible, l'utiliser
        if self.client:
            try:
                prompt = f"""Tu es un assistant d'achat en Tunisie.

Requête utilisateur : "{query}"
Quantité demandée : {quantity}

Fournisseur sélectionné :
- Nom : {best_supplier['supplier_name']}
- Ville : {best_supplier['city']}
- Produit : {best_supplier['product_name']} ({best_supplier['brand']})
- Prix unitaire : {best_supplier['unit_price']} TND
- Prix total : {best_supplier['total_price']} TND

Explique en 2-3 phrases courtes pourquoi ce fournisseur est le meilleur choix (prix, pertinence, localisation)."""

                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=150
                )
                
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"⚠️ Erreur GROQ : {e}")
        
        # Fallback : explication simple sans IA
        return self._generate_simple_explanation(best_supplier, query, quantity)
    
    def _generate_simple_explanation(self, best_supplier: Dict, query: str, quantity: int) -> str:
        """Génère une explication simple sans IA"""
        return (
            f"Ce fournisseur propose le meilleur rapport qualité-prix pour votre recherche '{query}'. "
            f"Avec un prix total de {best_supplier['total_price']} TND pour {quantity} unités, "
            f"{best_supplier['supplier_name']} à {best_supplier['city']} offre le tarif le plus compétitif "
            f"pour le produit {best_supplier['product_name']} de la marque {best_supplier['brand']}."
        )
