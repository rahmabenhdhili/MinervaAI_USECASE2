from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import tempfile
from typing import List

from .config_usershop import settings
from .models_usershop import (
    Product, 
    RecommendationRequest, 
    RecommendationResponse, 
    ProductSearchRequest,
    ProductComparisonRequest,
    ComparisonResponse
)
from .database_usershop import db
from .llm_service_v2_usershop import advanced_llm_service
from .data_loader_usershop import data_loader

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="Système de Recommandation de Produits Usershop",
    description="API pour recommandations de produits avec IA et base vectorielle",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage de l'application"""
    try:
        logger.info("🚀 Démarrage de l'application Usershop...")
        
        # Initialiser la collection Qdrant
        await db.initialize_collection()
        
        # Vérifier si des produits existent déjà
        collection_info = db.get_collection_info()
        products_count = collection_info.get('points_count', 0)
        
        logger.info(f"📊 Produits actuels dans Qdrant: {products_count}")
        
        # Si aucun produit, charger automatiquement depuis /data
        if products_count == 0:
            logger.info("📁 Aucun produit trouvé. Chargement automatique depuis /data...")
            
            try:
                # Essayer plusieurs chemins possibles
                possible_paths = [
                    "data",           # Depuis backend/
                    "../data",        # Depuis la racine
                    "../../data"      # Au cas où
                ]
                
                products = None
                load_stats = None
                
                for data_path in possible_paths:
                    try:
                        products, load_stats = data_loader.load_all_csv_from_directory(data_path)
                        if products:
                            logger.info(f"✅ Produits trouvés dans '{data_path}'")
                            break
                    except Exception:
                        continue
                
                if products:
                    logger.info(f"✅ {len(products)} produits trouvés")
                    
                    # Ajouter à Qdrant
                    upload_stats = await db.add_products(products)
                    
                    logger.info(f"✅ {len(products)} produits chargés automatiquement au démarrage")
                else:
                    logger.warning("⚠️ Aucun produit trouvé dans les dossiers data")
                    
            except Exception as e:
                logger.warning(f"⚠️ Impossible de charger automatiquement les produits: {e}")
                logger.info("💡 Vous pouvez charger manuellement via /load-from-directory")
        else:
            logger.info(f"✅ {products_count} produits déjà présents dans Qdrant")
        
        logger.info("✅ Application Usershop démarrée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        # Ne pas bloquer le démarrage si le chargement échoue
        logger.info("⚠️ L'application démarre sans produits pré-chargés")

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    try:
        collection_info = db.get_collection_info()
        products_count = collection_info.get('points_count', 0)
    except:
        products_count = 0
    
    return {
        "message": "Système de Recommandation de Produits Usershop avec IA",
        "version": "2.0.0",
        "service": "usershop",
        "products_loaded": products_count,
        "status": "ready" if products_count > 0 else "no_products",
        "endpoints": {
            "recommend": "/recommend",
            "compare": "/compare",
            "product": "/product/{id}",
            "add_products": "/add-products",
            "load_from_directory": "/load-from-directory",
            "search": "/search",
            "stats": "/stats"
        }
    }

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Génère des recommandations ultra-précises
    Processus optimisé : 100 résultats → filtrage avancé → tous les produits filtrés
    """
    try:
        logger.info(f"🔍 Nouvelle recherche avec critères: {request.dict()}")
        
        # Créer la requête de recherche vectorielle
        search_query = advanced_llm_service.create_search_query(request.dict())
        
        # Étape 1: Recherche vectorielle large (100 produits pour meilleure couverture)
        search_limit = 100
        logger.info(f"📡 Recherche vectorielle de {search_limit} produits similaires...")
        similar_products = await db.search_similar_products(search_query, limit=search_limit)
        
        if not similar_products:
            raise HTTPException(
                status_code=404, 
                detail="Aucun produit trouvé. Essayez avec d'autres critères."
            )
        
        logger.info(f"📊 {len(similar_products)} produits trouvés par recherche vectorielle")
        total_found = len(similar_products)
        
        # Étape 2: Sélection ultra-précise avec filtrage prix
        logger.info(f"🎯 Filtrage avancé et scoring...")
        best_products = advanced_llm_service.select_best_products(
            similar_products, 
            request.dict(), 
            limit=request.limit  # None = tous les produits
        )
        
        if not best_products:
            raise HTTPException(
                status_code=404, 
                detail="Aucun produit ne correspond aux critères de prix spécifiés."
            )
        
        total_after_filter = len(best_products)
        logger.info(f"✨ {total_after_filter} produits sélectionnés après filtrage avancé")
        
        # Produit principal (meilleur score)
        target_product = best_products[0]
        logger.info(f"🎯 Produit principal: {target_product.get('name')[:50]} (score: {target_product.get('relevance_score', 0):.2f})")
        
        # Étape 3: Génération des recommandations avec IA
        logger.info(f"🤖 Génération des descriptions et recommandations...")
        recommendations = await advanced_llm_service.generate_recommendations(
            target_product, 
            best_products[1:],  # Les autres comme recommandations
            request.dict(),
            total_found,
            total_after_filter
        )
        
        logger.info(f"✅ Recommandations générées: 1 principal + {len(recommendations.recommendations)} similaires")
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération de recommandations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/product/{product_id}")
async def get_product(product_id: str):
    """
    Récupère les détails d'un produit par son ID
    """
    try:
        product = await db.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du produit: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.post("/search")
async def search_products(request: ProductSearchRequest):
    """
    Recherche des produits par requête textuelle
    """
    try:
        products = await db.search_similar_products(request.query, request.limit)
        
        return {
            "query": request.query,
            "results": products,
            "count": len(products)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.post("/add-products")
async def add_products_from_csv(file: UploadFile = File(...)):
    """
    Charge des produits depuis un fichier CSV avec suivi détaillé
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Le fichier doit être un CSV")
        
        # Sauvegarder temporairement le fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Valider le format du CSV
            if not data_loader.validate_csv_format(tmp_file_path):
                raise HTTPException(
                    status_code=400, 
                    detail="Format CSV invalide. Colonnes requises: url, name, category, brand, img, description, price"
                )
            
            # Charger les produits avec statistiques
            products, load_stats = data_loader.load_products_from_csv(tmp_file_path)
            
            if not products:
                raise HTTPException(status_code=400, detail="Aucun produit valide trouvé dans le CSV")
            
            # Ajouter les produits à la base vectorielle
            upload_stats = await db.add_products(products)
            
            # Combiner les statistiques
            combined_stats = {
                "message": f"{len(products)} produits ajoutés avec succès",
                "count": len(products),
                "loading_stats": load_stats,
                "upload_stats": upload_stats,
                "all_steps": load_stats["steps"] + upload_stats["steps"]
            }
            
            return combined_stats
            
        finally:
            # Nettoyer le fichier temporaire
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des produits: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.post("/load-from-directory")
async def load_products_from_directory(directory: str = "data"):
    """
    Charge tous les fichiers CSV depuis un dossier avec suivi détaillé
    """
    try:
        logger.info(f"🚀 Chargement des produits depuis le dossier '{directory}'...")
        
        # Charger tous les CSV du dossier
        products, load_stats = data_loader.load_all_csv_from_directory(directory)
        
        if not products:
            raise HTTPException(
                status_code=404, 
                detail=f"Aucun produit trouvé dans le dossier '{directory}'"
            )
        
        # Ajouter les produits à Qdrant Cloud
        upload_stats = await db.add_products(products)
        
        # Informations sur la collection
        collection_info = db.get_collection_info()
        
        # Combiner toutes les statistiques
        result = {
            "message": f"✅ {len(products)} produits chargés avec succès depuis {load_stats['files_processed']} fichier(s)",
            "total_products": len(products),
            "files_processed": load_stats['files_processed'],
            "collection_info": collection_info,
            "loading_stats": load_stats,
            "upload_stats": upload_stats,
            "all_steps": load_stats["steps"] + upload_stats["steps"]
        }
        
        logger.info(f"✅ Chargement terminé: {len(products)} produits")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "healthy", "message": "API Usershop fonctionnelle", "service": "usershop"}

@app.get("/stats")
async def get_stats():
    """Récupère les statistiques de la base de données"""
    try:
        collection_info = db.get_collection_info()
        return {
            "status": "ok",
            "service": "usershop",
            "collection": collection_info,
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.GROQ_MODEL
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.post("/compare", response_model=ComparisonResponse)
async def compare_products(request: ProductComparisonRequest):
    """
    Compare deux produits de manière intelligente avec l'IA
    Analyse technique, avantages/inconvénients, et recommandation
    """
    try:
        logger.info(f"🔄 Demande de comparaison: {request.product_id_1} vs {request.product_id_2}")
        
        # Récupérer les deux produits
        product_1 = await db.get_product_by_id(request.product_id_1)
        product_2 = await db.get_product_by_id(request.product_id_2)
        
        if not product_1:
            raise HTTPException(status_code=404, detail=f"Produit 1 non trouvé: {request.product_id_1}")
        
        if not product_2:
            raise HTTPException(status_code=404, detail=f"Produit 2 non trouvé: {request.product_id_2}")
        
        # Générer la comparaison avec l'IA
        comparison_data = await advanced_llm_service.compare_products(product_1, product_2)
        
        # Créer la réponse structurée
        response = ComparisonResponse(**comparison_data)
        
        logger.info(f"✅ Comparaison générée: Recommandation = {response.final_recommendation}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la comparaison: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_usershop:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
