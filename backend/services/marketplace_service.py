"""
Service Marketplace - Gestion de la boutique e-commerce de l'utilisateur
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import uuid


class MarketplaceService:
    """Service pour gérer la marketplace de l'utilisateur"""
    
    def __init__(self, data_file: str = "marketplace_products.json", debug: bool = False):
        self.data_file = data_file
        self.debug = debug
        self.products = self._load_products()
        
        if debug:
            print(f"✅ Marketplace Service initialisé")
            print(f"   📦 {len(self.products)} produits dans la marketplace")
    
    def _load_products(self) -> List[Dict]:
        """Charge les produits depuis le fichier JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                if self.debug:
                    print(f"⚠️ Erreur chargement: {e}")
                return []
        return []
    
    def _save_products(self) -> bool:
        """Sauvegarde les produits dans le fichier JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur sauvegarde: {e}")
            return False
    
    def add_product(
        self,
        name: str,
        description: str,
        price: float,
        image_url: str,
        category: str = "general",
        metadata: Dict = None
    ) -> Dict:
        """
        Ajoute un produit à la marketplace
        
        Args:
            name: Nom du produit
            description: Description du produit
            price: Prix de vente du produit
            image_url: URL de l'image
            category: Catégorie du produit
            metadata: Métadonnées additionnelles (doit contenir original_price pour le coût)
        
        Returns:
            Produit ajouté avec son ID
        """
        
        # Calculer le coût et le bénéfice
        original_price = metadata.get('original_price', price) if metadata else price
        cost = float(original_price)
        profit = float(price) - cost
        profit_margin = (profit / cost * 100) if cost > 0 else 0
        
        product = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "price": price,  # Prix de vente
            "cost": cost,    # Coût d'achat
            "profit": profit,  # Bénéfice unitaire
            "profit_margin": profit_margin,  # Marge en %
            "image_url": image_url,
            "category": category,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "clicks": 0,  # Tracking des clics
            "views": 0    # Tracking des vues
        }
        
        self.products.append(product)
        
        if self._save_products():
            if self.debug:
                print(f"✅ Produit ajouté: {name} (${price})")
            return {
                "success": True,
                "product": product,
                "message": "Produit ajouté avec succès"
            }
        else:
            return {
                "success": False,
                "error": "Erreur lors de la sauvegarde"
            }
    
    def get_all_products(self) -> List[Dict]:
        """Récupère tous les produits de la marketplace"""
        return [p for p in self.products if p.get("status") == "active"]
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Récupère un produit par son ID"""
        for product in self.products:
            if product["id"] == product_id:
                return product
        return None
    
    def update_product(
        self,
        product_id: str,
        name: str = None,
        description: str = None,
        price: float = None,
        image_url: str = None,
        category: str = None
    ) -> Dict:
        """
        Met à jour un produit existant
        
        Args:
            product_id: ID du produit
            name: Nouveau nom (optionnel)
            description: Nouvelle description (optionnel)
            price: Nouveau prix (optionnel)
            image_url: Nouvelle image (optionnel)
            category: Nouvelle catégorie (optionnel)
        
        Returns:
            Résultat de la mise à jour
        """
        
        for i, product in enumerate(self.products):
            if product["id"] == product_id:
                if name is not None:
                    product["name"] = name
                if description is not None:
                    product["description"] = description
                if price is not None:
                    product["price"] = price
                if image_url is not None:
                    product["image_url"] = image_url
                if category is not None:
                    product["category"] = category
                
                product["updated_at"] = datetime.now().isoformat()
                
                if self._save_products():
                    if self.debug:
                        print(f"✅ Produit mis à jour: {product['name']}")
                    return {
                        "success": True,
                        "product": product,
                        "message": "Produit mis à jour avec succès"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Erreur lors de la sauvegarde"
                    }
        
        return {
            "success": False,
            "error": "Produit non trouvé"
        }
    
    def delete_product(self, product_id: str) -> Dict:
        """
        Supprime un produit (soft delete)
        
        Args:
            product_id: ID du produit
        
        Returns:
            Résultat de la suppression
        """
        
        for product in self.products:
            if product["id"] == product_id:
                product["status"] = "deleted"
                product["updated_at"] = datetime.now().isoformat()
                
                if self._save_products():
                    if self.debug:
                        print(f"✅ Produit supprimé: {product['name']}")
                    return {
                        "success": True,
                        "message": "Produit supprimé avec succès"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Erreur lors de la sauvegarde"
                    }
        
        return {
            "success": False,
            "error": "Produit non trouvé"
        }
    
    def get_stats(self) -> Dict:
        """Récupère les statistiques de la marketplace"""
        active_products = [p for p in self.products if p.get("status") == "active"]
        
        total_value = sum(p.get("price", 0) for p in active_products)
        total_clicks = sum(p.get("clicks", 0) for p in active_products)
        total_views = sum(p.get("views", 0) for p in active_products)
        
        categories = {}
        for product in active_products:
            cat = product.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_products": len(active_products),
            "total_value": total_value,
            "total_clicks": total_clicks,
            "total_views": total_views,
            "categories": categories,
            "last_updated": datetime.now().isoformat()
        }
    
    def increment_click(self, product_id: str) -> Dict:
        """
        Incrémente le compteur de clics d'un produit
        
        Args:
            product_id: ID du produit
        
        Returns:
            Résultat de l'opération
        """
        for product in self.products:
            if product["id"] == product_id:
                product["clicks"] = product.get("clicks", 0) + 1
                product["updated_at"] = datetime.now().isoformat()
                
                if self._save_products():
                    if self.debug:
                        print(f"✅ Clic enregistré: {product['name']} ({product['clicks']} clics)")
                    return {
                        "success": True,
                        "clicks": product["clicks"]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Erreur lors de la sauvegarde"
                    }
        
        return {
            "success": False,
            "error": "Produit non trouvé"
        }
    
    def increment_view(self, product_id: str) -> Dict:
        """
        Incrémente le compteur de vues d'un produit
        
        Args:
            product_id: ID du produit
        
        Returns:
            Résultat de l'opération
        """
        for product in self.products:
            if product["id"] == product_id:
                product["views"] = product.get("views", 0) + 1
                product["updated_at"] = datetime.now().isoformat()
                
                if self._save_products():
                    return {
                        "success": True,
                        "views": product["views"]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Erreur lors de la sauvegarde"
                    }
        
        return {
            "success": False,
            "error": "Produit non trouvé"
        }
