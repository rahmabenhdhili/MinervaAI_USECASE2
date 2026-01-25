from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import pandas as pd
import tempfile
import os
from typing import List, Dict, Any

from .models import (
    RecommendationRequest, 
    RecommendationResponse, 
    ProductRecommendation,
    ProductSearchRequest
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="Système de Recommandation de Produits",
    description="API pour recommandations de produits avec IA et base vectorielle",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire pour les tests
products_db = []

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage de l'application"""
    logger.info("Application démarrée avec succès (mode simple)")

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "Système de Recommandation de Produits avec IA (Mode Simple)",
        "version": "1.0.0",
        "mode": "simple",
        "products_count": len(products_db),
        "endpoints": {
            "recommend": "/recommend",
            "product": "/product/{id}",
            "add_products": "/add-products",
            "search": "/search"
        }
    }

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Génère des recommandations basées sur les critères fournis (version simplifiée)
    """
    try:
        if not products_db:
            raise HTTPException(status_code=404, detail="Aucun produit en base. Veuillez d'abord importer des produits.")
        
        # Recherche simple par mots-clés
        matching_products = []
        search_terms = []
        
        if request.name:
            search_terms.extend(request.name.lower().split())
        if request.category:
            search_terms.extend(request.category.lower().split())
        if request.description:
            search_terms.extend(request.description.lower().split())
        
        for product in products_db:
            score = 0
            product_text = f"{product['name']} {product['category']} {product['description']}".lower()
            
            for term in search_terms:
                if term in product_text:
                    score += 1
            
            if score > 0:
                product_copy = product.copy()
                product_copy['score'] = score / len(search_terms) if search_terms else 0
                matching_products.append(product_copy)
        
        # Trier par score
        matching_products.sort(key=lambda x: x['score'], reverse=True)
        
        if not matching_products:
            # Si aucun match, prendre les premiers produits
            matching_products = products_db[:5]
        
        # Prendre le premier comme produit principal
        main_product = matching_products[0]
        
        # Générer une description enrichie simple
        description = f"""
        {main_product['name']} de la marque {main_product['brand']} est un excellent produit dans la catégorie {main_product['category']}. 
        {main_product['description']} 
        
        Ce produit se distingue par sa qualité et son rapport qualité-prix exceptionnel à {main_product['price']}. 
        Idéal pour ceux qui recherchent performance et fiabilité.
        """.strip()
        
        # Créer les recommandations (exclure le produit principal)
        recommendations = []
        for product in matching_products[1:6]:  # Prendre 5 recommandations max
            rec = ProductRecommendation(
                name=product['name'],
                category=product['category'],
                brand=product['brand'],
                price=product['price'],
                img=product['img'],
                url=product['url']
            )
            recommendations.append(rec)
        
        return RecommendationResponse(
            product_description=description,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération de recommandations: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.get("/product/{product_id}")
async def get_product(product_id: str):
    """
    Récupère les détails d'un produit par son ID
    """
    try:
        for product in products_db:
            if product.get('id') == product_id:
                return product
        
        raise HTTPException(status_code=404, detail="Produit non trouvé")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du produit: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.post("/search")
async def search_products(request: ProductSearchRequest):
    """
    Recherche des produits par requête textuelle (version simplifiée)
    """
    try:
        if not products_db:
            return {"query": request.query, "results": [], "count": 0}
        
        query_lower = request.query.lower()
        matching_products = []
        
        for product in products_db:
            product_text = f"{product['name']} {product['category']} {product['description']} {product['brand']}".lower()
            if query_lower in product_text:
                matching_products.append(product)
        
        # Limiter les résultats
        matching_products = matching_products[:request.limit]
        
        return {
            "query": request.query,
            "results": matching_products,
            "count": len(matching_products)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.post("/add-products")
async def add_products_from_csv(file: UploadFile = File(...)):
    """
    Charge des produits depuis un fichier CSV (version simplifiée)
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Le fichier doit être un CSV")
        
        # Lire le contenu du fichier
        content = await file.read()
        
        # Sauvegarder temporairement le fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Lire le CSV
            df = pd.read_csv(tmp_file_path, sep=',')
            
            # Vérifier les colonnes requises
            required_columns = ['url', 'name', 'category', 'brand', 'img', 'description', 'price']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Colonnes manquantes dans le CSV: {missing_columns}"
                )
            
            # Nettoyer et convertir les données
            df = df.dropna(subset=required_columns)
            df = df.fillna('')
            
            # Vider la base actuelle et ajouter les nouveaux produits
            products_db.clear()
            
            for index, row in df.iterrows():
                product = {
                    'id': str(index),
                    'url': str(row['url']).strip(),
                    'name': str(row['name']).strip(),
                    'category': str(row['category']).strip(),
                    'brand': str(row['brand']).strip(),
                    'img': str(row['img']).strip(),
                    'description': str(row['description']).strip(),
                    'price': str(row['price']).strip()
                }
                products_db.append(product)
            
            logger.info(f"{len(products_db)} produits ajoutés à la base")
            
            return {
                "message": f"{len(products_db)} produits ajoutés avec succès",
                "count": len(products_db)
            }
            
        finally:
            # Nettoyer le fichier temporaire
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des produits: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}")

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy", 
        "message": "API fonctionnelle (mode simple)",
        "products_count": len(products_db)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.simple_main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )