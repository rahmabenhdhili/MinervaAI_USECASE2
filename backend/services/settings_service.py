"""
Service de gestion des paramètres de la marketplace
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime


class SettingsService:
    """Service pour gérer les paramètres de la marketplace du vendeur"""
    
    def __init__(self, data_file: str = "marketplace_settings.json", debug: bool = False):
        self.data_file = data_file
        self.debug = debug
        self.settings = self._load_settings()
        
        if debug:
            print(f"✅ Settings Service initialisé")
            print(f"   🏪 Marketplace: {self.settings.get('marketplace_name', 'Ma Marketplace')}")
    
    def _load_settings(self) -> Dict:
        """Charge les paramètres depuis le fichier JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                if self.debug:
                    print(f"⚠️ Erreur chargement settings: {e}")
                return self._get_default_settings()
        return self._get_default_settings()
    
    def _get_default_settings(self) -> Dict:
        """Retourne les paramètres par défaut"""
        return {
            "marketplace_name": "Ma Marketplace",
            "marketplace_logo": "https://via.placeholder.com/200x80?text=Logo",
            "marketplace_description": "Votre boutique e-commerce",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _save_settings(self) -> bool:
        """Sauvegarde les paramètres dans le fichier JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur sauvegarde settings: {e}")
            return False
    
    def get_settings(self) -> Dict:
        """Récupère tous les paramètres"""
        return self.settings
    
    def update_settings(
        self,
        marketplace_name: str = None,
        marketplace_logo: str = None,
        marketplace_description: str = None
    ) -> Dict:
        """
        Met à jour les paramètres de la marketplace
        
        Args:
            marketplace_name: Nouveau nom (optionnel)
            marketplace_logo: Nouvelle URL du logo (optionnel)
            marketplace_description: Nouvelle description (optionnel)
        
        Returns:
            Résultat de la mise à jour
        """
        
        if marketplace_name is not None:
            self.settings["marketplace_name"] = marketplace_name
        
        if marketplace_logo is not None:
            self.settings["marketplace_logo"] = marketplace_logo
        
        if marketplace_description is not None:
            self.settings["marketplace_description"] = marketplace_description
        
        self.settings["updated_at"] = datetime.now().isoformat()
        
        if self._save_settings():
            if self.debug:
                print(f"✅ Paramètres mis à jour: {self.settings['marketplace_name']}")
            return {
                "success": True,
                "settings": self.settings,
                "message": "Paramètres mis à jour avec succès"
            }
        else:
            return {
                "success": False,
                "error": "Erreur lors de la sauvegarde"
            }
    
    def reset_settings(self) -> Dict:
        """
        Réinitialise les paramètres aux valeurs par défaut
        
        Returns:
            Résultat de la réinitialisation
        """
        self.settings = self._get_default_settings()
        
        if self._save_settings():
            if self.debug:
                print(f"✅ Paramètres réinitialisés")
            return {
                "success": True,
                "settings": self.settings,
                "message": "Paramètres réinitialisés avec succès"
            }
        else:
            return {
                "success": False,
                "error": "Erreur lors de la sauvegarde"
            }
