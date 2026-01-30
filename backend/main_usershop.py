#!/usr/bin/env python3
"""
Point d'entrée principal de l'application Usershop
Système de Recommandation de Produits avec IA

Usage:
    python main_usershop.py              # Démarre le serveur
    python main_usershop.py --help       # Affiche l'aide
"""

import sys
import os

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.config_usershop import settings

def main():
    """Démarre le serveur FastAPI"""
    print("=" * 60)
    print("🚀 Système de Recommandation Usershop avec IA")
    print("=" * 60)
    print(f"📡 Serveur: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔧 Mode: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    print(f"🤖 LLM: {settings.GROQ_MODEL}")
    print(f"🗄️  Collection: {settings.QDRANT_COLLECTION_NAME}")
    print(f"🏷️  Service: Usershop")
    print("=" * 60)
    print("💡 Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 60)
    print()
    
    try:
        uvicorn.run(
            "app.main_usershop:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt du serveur Usershop...")
        print("✅ Serveur arrêté proprement")
    except Exception as e:
        print(f"\n❌ Erreur lors du démarrage: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Vérifier les arguments
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print(__doc__)
        print("\nOptions:")
        print("  --help, -h    Affiche cette aide")
        print("\nConfiguration:")
        print(f"  Host: {settings.HOST}")
        print(f"  Port: {settings.PORT}")
        print(f"  Debug: {settings.DEBUG}")
        print(f"  Service: Usershop")
        print("\nPour modifier la configuration, éditez le fichier .env")
        sys.exit(0)
    
    main()
