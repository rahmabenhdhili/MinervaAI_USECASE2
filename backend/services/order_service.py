"""
Service de gestion des commandes
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import uuid


class OrderService:
    """Service pour gérer les commandes de la marketplace"""
    
    def __init__(self, data_file: str = "orders.json", debug: bool = False):
        self.data_file = data_file
        self.debug = debug
        self.orders = self._load_orders()
        
        if debug:
            print(f"✅ Order Service initialisé")
            print(f"   📦 {len(self.orders)} commandes")
    
    def _load_orders(self) -> List[Dict]:
        """Charge les commandes depuis le fichier JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                if self.debug:
                    print(f"⚠️ Erreur chargement: {e}")
                return []
        return []
    
    def _save_orders(self) -> bool:
        """Sauvegarde les commandes dans le fichier JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.orders, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur sauvegarde: {e}")
            return False
    
    def create_order(
        self,
        customer_name: str,
        customer_phone: str,
        shipping_address: Dict,
        items: List[Dict],
        payment_method: str = "card"
    ) -> Dict:
        """
        Crée une nouvelle commande (automatiquement livrée)
        
        Args:
            customer_name: Nom du client
            customer_phone: Téléphone du client
            shipping_address: Adresse de livraison
            items: Liste des produits commandés (avec cost et profit)
            payment_method: Méthode de paiement
        
        Returns:
            Commande créée
        """
        
        # Calculer les totaux
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        total_cost = sum(item.get('cost', item['price']) * item['quantity'] for item in items)
        shipping_cost = 0  # Livraison gratuite
        tax = 0  # Pas de taxe
        total = subtotal + shipping_cost + tax
        total_profit = total - total_cost
        
        order = {
            "id": str(uuid.uuid4()),
            "order_number": f"ORD-{len(self.orders) + 1:05d}",
            "customer": {
                "name": customer_name,
                "phone": customer_phone
            },
            "shipping_address": shipping_address,
            "items": items,
            "pricing": {
                "subtotal": round(subtotal, 2),
                "shipping": round(shipping_cost, 2),
                "tax": round(tax, 2),
                "total": round(total, 2),
                "cost": round(total_cost, 2),  # Coût total
                "profit": round(total_profit, 2)  # Bénéfice total
            },
            "payment_method": payment_method,
            "status": "delivered",  # Automatiquement livrée
            "tracking_number": f"TRK-{len(self.orders) + 1:08d}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "delivered_at": datetime.now().isoformat(),  # Livrée immédiatement
            "status_history": [
                {
                    "status": "delivered",
                    "timestamp": datetime.now().isoformat(),
                    "note": "Commande créée et livrée"
                }
            ]
        }
        
        self.orders.append(order)
        
        if self._save_orders():
            if self.debug:
                print(f"✅ Commande créée: {order['order_number']} (${total:.2f})")
            return {
                "success": True,
                "order": order,
                "message": "Commande créée avec succès"
            }
        else:
            return {
                "success": False,
                "error": "Erreur lors de la sauvegarde"
            }
    
    def get_all_orders(self) -> List[Dict]:
        """Récupère toutes les commandes"""
        return sorted(self.orders, key=lambda x: x['created_at'], reverse=True)
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Récupère une commande par son ID"""
        for order in self.orders:
            if order["id"] == order_id:
                return order
        return None
    
    def get_order_by_number(self, order_number: str) -> Optional[Dict]:
        """Récupère une commande par son numéro"""
        for order in self.orders:
            if order["order_number"] == order_number:
                return order
        return None
    
    def update_order_status(
        self,
        order_id: str,
        status: str,
        tracking_number: str = None,
        note: str = None
    ) -> Dict:
        """
        Met à jour le statut d'une commande
        
        Args:
            order_id: ID de la commande
            status: Nouveau statut
            tracking_number: Numéro de suivi (optionnel)
            note: Note (optionnel)
        
        Returns:
            Résultat de la mise à jour
        """
        
        for order in self.orders:
            if order["id"] == order_id:
                order["status"] = status
                order["updated_at"] = datetime.now().isoformat()
                
                if tracking_number:
                    order["tracking_number"] = tracking_number
                
                # Ajouter à l'historique
                order["status_history"].append({
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                    "note": note or f"Statut changé en {status}"
                })
                
                if self._save_orders():
                    if self.debug:
                        print(f"✅ Commande {order['order_number']} → {status}")
                    return {
                        "success": True,
                        "order": order,
                        "message": "Statut mis à jour"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Erreur lors de la sauvegarde"
                    }
        
        return {
            "success": False,
            "error": "Commande non trouvée"
        }
    
    def get_stats(self) -> Dict:
        """Récupère les statistiques des commandes (uniquement livrées)"""
        # Filtrer uniquement les commandes livrées
        delivered_orders = [o for o in self.orders if o.get("status") == "delivered"]
        total_orders = len(delivered_orders)
        
        # Calculer revenus et bénéfices
        total_revenue = 0
        total_profit = 0
        
        for order in delivered_orders:
            total_revenue += order["pricing"]["total"]
            total_profit += order["pricing"].get("profit", 0)
        
        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin": round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 2),
            "last_updated": datetime.now().isoformat()
        }
    
    def get_delivered_orders(self) -> List[Dict]:
        """Récupère uniquement les commandes livrées"""
        return [o for o in self.orders if o.get("status") == "delivered"]
