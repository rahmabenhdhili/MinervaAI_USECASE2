"""
Script de démarrage rapide pour tester le système
Usage: python scripts/quick_start.py
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.recommendation_service import RecommendationService
from models import SearchQuery


async def quick_test():
    """Test rapide du système"""
    
    print("=" * 70)
    print("🚀 QUICK START - Système de Recommandation IA")
    print("=" * 70)
    
    # Initialiser
    print("\n⏳ Initialisation du système...")
    service = RecommendationService()
    await service.initialize()
    print("✅ Système prêt!\n")
    
    # Test simple
    query = SearchQuery(
        query="laptop gaming RTX 4060",
        max_results=3
    )
    
    print(f"🔍 Recherche: '{query.query}'")
    print("-" * 70)
    
    result = await service.get_recommendations(query)
    
    # Afficher les résultats
    print(f"\n📊 INTENTION DÉTECTÉE:")
    print(f"   Type: {result.intent.product_type}")
    print(f"   Usage: {result.intent.usage or 'Non spécifié'}")
    print(f"   Features: {', '.join(result.intent.key_features) if result.intent.key_features else 'Aucune'}")
    
    print(f"\n💡 RECOMMANDATION:")
    print(f"   {result.summary}")
    
    print(f"\n🛍️ TOP {len(result.recommendations)} PRODUITS:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"\n   {i}. {rec.product.name}")
        print(f"      💰 ${rec.product.price:.2f}")
        print(f"      📊 Score: {rec.similarity_score:.1%}")
        if rec.product.rating:
            print(f"      ⭐ {rec.product.rating}/5")
    
    print("\n" + "=" * 70)
    print("✅ Test terminé avec succès!")
    print("=" * 70)
    
    print("\n💡 Prochaines étapes:")
    print("   1. Lancer le backend: uvicorn main:app --reload")
    print("   2. Lancer le frontend: cd frontend && npm start")
    print("   3. Ouvrir http://localhost:3000")


if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n\n⚠️ Arrêt par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
