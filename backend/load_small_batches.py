#!/usr/bin/env python3
"""
Script pour charger les produits par petits lots avec gestion d'erreurs
"""

import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db
from app.data_loader import data_loader

async def load_in_small_batches():
    """Charge les produits par petits lots"""
    print("🚀 Chargement optimisé des produits")
    print("=" * 60)
    
    try:
        # Initialiser la collection
        print("\n⚙️ Initialisation...")
        await db.initialize_collection()
        
        # Compter les produits existants
        try:
            count_result = db.client.count(collection_name=db.collection_name)
            existing_count = count_result.count
        except:
            existing_count = 0
        
        print(f"📊 Produits actuels: {existing_count}")
        
        # Charger les produits depuis les fichiers
        print("\n📁 Lecture des fichiers CSV...")
        products, load_stats = data_loader.load_all_csv_from_directory("../data")
        total_products = len(products)
        
        print(f"📦 Produits à charger: {total_products}")
        
        if existing_count >= total_products:
            print(f"\n✅ Tous les produits sont déjà chargés!")
            return True
        
        # Charger par lots de 1000 produits
        batch_size = 1000
        total_batches = (total_products - 1) // batch_size + 1
        
        print(f"\n🔄 Chargement en {total_batches} lots de {batch_size} produits...")
        
        for i in range(0, total_products, batch_size):
            batch_products = products[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"\n📦 Lot {batch_num}/{total_batches} ({len(batch_products)} produits)...")
            
            try:
                # Charger ce lot
                upload_stats = await db.add_products(batch_products)
                
                # Afficher quelques étapes
                for step in upload_stats["steps"][-3:]:
                    print(f"  {step}")
                
                # Vérifier le compte
                count_result = db.client.count(collection_name=db.collection_name)
                current_count = count_result.count
                print(f"  ✅ Total actuel: {current_count} produits")
                
                # Petite pause entre les lots
                if batch_num < total_batches:
                    time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Erreur sur le lot {batch_num}: {e}")
                print(f"  ⏭️ Passage au lot suivant...")
                continue
        
        # Vérifier le résultat final
        count_result = db.client.count(collection_name=db.collection_name)
        final_count = count_result.count
        
        print("\n" + "=" * 60)
        print(f"✅ CHARGEMENT TERMINÉ!")
        print(f"📊 Total: {final_count} produits dans Qdrant Cloud")
        print(f"📈 Taux de réussite: {(final_count/total_products)*100:.1f}%")
        
        if final_count >= total_products * 0.95:  # 95% de réussite
            print("\n🎉 Le système est prêt!")
            print("\n💡 Prochaines étapes:")
            print("   1. Démarrer le backend: python run.py")
            print("   2. Démarrer le frontend: cd ../frontend && npm start")
            return True
        else:
            print(f"\n⚠️ Seulement {final_count}/{total_products} produits chargés")
            print("💡 Relancez le script pour charger les produits manquants")
            return False
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(load_in_small_batches())
    sys.exit(0 if success else 1)