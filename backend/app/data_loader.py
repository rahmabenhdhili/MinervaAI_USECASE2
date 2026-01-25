import pandas as pd
import logging
from typing import List, Dict, Any
from .models import Product
import os
import glob

logger = logging.getLogger(__name__)

class DataLoader:
    """Classe pour charger et traiter les données CSV avec optimisation"""
    
    @staticmethod
    def load_products_from_csv(file_path: str) -> tuple[List[Product], Dict[str, Any]]:
        """
        Charge les produits depuis un fichier CSV avec suivi des étapes
        Retourne: (liste de produits, statistiques du chargement)
        """
        stats = {
            "total_rows": 0,
            "valid_products": 0,
            "invalid_rows": 0,
            "duplicates_removed": 0,
            "steps": []
        }
        
        try:
            # Étape 1: Lecture du fichier
            stats["steps"].append("📖 Lecture du fichier CSV...")
            logger.info(f"Lecture du fichier: {file_path}")
            
            df = pd.read_csv(file_path, sep=',')
            stats["total_rows"] = len(df)
            stats["steps"].append(f"✅ {stats['total_rows']} lignes lues")
            
            # Étape 2: Validation des colonnes
            stats["steps"].append("🔍 Validation des colonnes...")
            required_columns = ['url', 'name', 'category', 'brand', 'img', 'description', 'price']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Colonnes manquantes: {missing_columns}")
            
            stats["steps"].append(f"✅ Toutes les colonnes requises présentes")
            
            # Étape 3: Nettoyage des données
            stats["steps"].append("🧹 Nettoyage des données...")
            initial_count = len(df)
            
            # Supprimer les lignes avec des valeurs manquantes dans les colonnes critiques
            df = df.dropna(subset=['name', 'category', 'description'])
            stats["invalid_rows"] = initial_count - len(df)
            
            # Remplir les valeurs manquantes non critiques
            df = df.fillna({
                'url': '',
                'brand': 'Non spécifié',
                'img': '',
                'price': 'Prix non disponible'
            })
            
            stats["steps"].append(f"✅ {stats['invalid_rows']} lignes invalides supprimées")
            
            # Étape 4: Suppression des doublons
            stats["steps"].append("🔄 Suppression des doublons...")
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['name', 'brand'], keep='first')
            stats["duplicates_removed"] = before_dedup - len(df)
            stats["steps"].append(f"✅ {stats['duplicates_removed']} doublons supprimés")
            
            # Étape 5: Optimisation des descriptions
            stats["steps"].append("⚡ Optimisation des descriptions...")
            df['description'] = df['description'].str.strip()
            df['description'] = df['description'].str[:500]  # Limiter à 500 caractères
            stats["steps"].append("✅ Descriptions optimisées")
            
            # Étape 6: Conversion en objets Product
            stats["steps"].append("📦 Création des objets produits...")
            products = []
            
            for _, row in df.iterrows():
                try:
                    product = Product(
                        url=str(row['url']).strip(),
                        name=str(row['name']).strip(),
                        category=str(row['category']).strip(),
                        brand=str(row['brand']).strip(),
                        img=str(row['img']).strip(),
                        description=str(row['description']).strip(),
                        price=str(row['price']).strip()
                    )
                    products.append(product)
                except Exception as e:
                    logger.warning(f"Erreur ligne {row.name}: {e}")
                    continue
            
            stats["valid_products"] = len(products)
            stats["steps"].append(f"✅ {stats['valid_products']} produits créés avec succès")
            
            logger.info(f"Chargement terminé: {stats['valid_products']} produits")
            return products, stats
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du CSV: {e}")
            stats["steps"].append(f"❌ Erreur: {str(e)}")
            raise
    
    @staticmethod
    def load_all_csv_from_directory(directory: str = "data") -> tuple[List[Product], Dict[str, Any]]:
        """
        Charge tous les fichiers CSV d'un dossier
        Retourne: (liste de tous les produits, statistiques globales)
        """
        all_products = []
        global_stats = {
            "files_processed": 0,
            "total_products": 0,
            "files": [],
            "steps": []
        }
        
        try:
            # Vérifier si le dossier existe
            if not os.path.exists(directory):
                raise ValueError(f"Le dossier '{directory}' n'existe pas")
            
            # Trouver tous les fichiers CSV
            csv_files = glob.glob(os.path.join(directory, "*.csv"))
            
            if not csv_files:
                raise ValueError(f"Aucun fichier CSV trouvé dans '{directory}'")
            
            global_stats["steps"].append(f"📁 {len(csv_files)} fichier(s) CSV trouvé(s)")
            
            # Charger chaque fichier
            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                global_stats["steps"].append(f"\n📄 Traitement de {filename}...")
                
                try:
                    products, file_stats = DataLoader.load_products_from_csv(csv_file)
                    all_products.extend(products)
                    
                    global_stats["files"].append({
                        "filename": filename,
                        "products": len(products),
                        "stats": file_stats
                    })
                    
                    global_stats["files_processed"] += 1
                    global_stats["steps"].extend(file_stats["steps"])
                    
                except Exception as e:
                    logger.error(f"Erreur avec {filename}: {e}")
                    global_stats["steps"].append(f"❌ Erreur avec {filename}: {str(e)}")
            
            global_stats["total_products"] = len(all_products)
            global_stats["steps"].append(f"\n✅ Total: {global_stats['total_products']} produits chargés depuis {global_stats['files_processed']} fichier(s)")
            
            return all_products, global_stats
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du dossier: {e}")
            global_stats["steps"].append(f"❌ Erreur: {str(e)}")
            raise
    
    @staticmethod
    def validate_csv_format(file_path: str) -> bool:
        """Valide le format du fichier CSV"""
        try:
            df = pd.read_csv(file_path, sep=',', nrows=1)
            required_columns = ['url', 'name', 'category', 'brand', 'img', 'description', 'price']
            return all(col in df.columns for col in required_columns)
        except Exception as e:
            logger.error(f"Erreur lors de la validation du CSV: {e}")
            return False

# Instance globale
data_loader = DataLoader()