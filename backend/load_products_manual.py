#!/usr/bin/env python3
"""
Script pour charger manuellement les produits dans Qdrant Cloud
"""

import sys
import os
import asyncio

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db
from app.data_loader import data_loader

async def load_products():
    """Charge les produits depuis le dossier data"""
    print("🚀 Chargement manuel des produits")
    print("=" * 60)
    
    try:
        # Initialiser la collection
        print("\n⚙️ Initialisation de la collection Qdrant...")
        await db.initialize_collection()
        print("✅ Collection initialisée")
        
        # Vérifier les produits existants
        collection_info = db.get_collection_info()
        existing_count = collection_info.get('points_count', 0)
        print(f"\n📊 Produits actuels dans Qdrant: {existing_count}")
        
        if existing_count > 0:
            response = input("\n⚠️ Des produits existent déjà. Continuer? (o/n): ")
            if response.lower() != 'o':
                print("❌ Opération annulée")
                return
        
        # Charger les produits depuis ../data
        print("\n📁 Chargement des fichiers CSV depuis ../data...")
        products, load_stats = data_loader.load_all_csv_from_directory("../data")
        
        if not products:
            print("❌ Aucun produit trouvé dans ../data")
            return
        
        print(f"\n✅ {len(products)} produits chargés depuis les fichiers CSV")
        
        # Afficher les étapes de chargement
        print("\n📋 Détails du chargement:")
        for step in load_stats["steps"]:
            print(f"  {step}")
        
        # Ajouter à Qdrant
        print(f"\n☁️ Upload vers Qdrant Cloud...")
        upload_stats = await db.add_products(products)
        
        # Afficher les étapes d'upload
        print("\n📋 Détails de l'upload:")
        for step in upload_stats["steps"]:
            print(f"  {step}")
        
        # Vérifier le résultat
        collection_info = db.get_collection_info()
        final_count = collection_info.get('points_count', 0)
        
        print("\n" + "=" * 60)
        print(f"✅ SUCCÈS!")
        print(f"📊 Total de produits dans Qdrant: {final_count}")
        print(f"📈 Nouveaux produits ajoutés: {upload_stats['success']}")
        print("\n🎉 Les produits sont maintenant disponibles pour la recherche!")
        print("💡 Vous pouvez maintenant utiliser le frontend pour rechercher des produits")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(load_products())