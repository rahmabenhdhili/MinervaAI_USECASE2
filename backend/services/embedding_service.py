"""
Embedding Service - Génération d'embeddings avec FastEmbed

⚠️ IMPORTANT: Utilise FastEmbed uniquement (pas de Hugging Face)
FastEmbed est optimisé pour Qdrant et offre de meilleures performances.
"""

from fastembed import TextEmbedding
from typing import List
import numpy as np


class EmbeddingService:
    """Service pour générer des embeddings sémantiques avec FastEmbed"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialise FastEmbed avec un modèle optimisé
        
        Modèles disponibles:
        - BAAI/bge-small-en-v1.5 (384 dim) - Rapide et efficace (DÉFAUT)
        - sentence-transformers/all-MiniLM-L6-v2 (384 dim)
        - BAAI/bge-base-en-v1.5 (768 dim) - Plus précis
        
        Args:
            model_name: Nom du modèle FastEmbed à utiliser
        """
        print(f"🧠 Initialisation FastEmbed: {model_name}")
        self.model = TextEmbedding(model_name=model_name)
        self.model_name = model_name
        
        # Déterminer la dimension du modèle
        test_embedding = list(self.model.embed(["test"]))[0]
        self.dimension = len(test_embedding)
        print(f"✅ FastEmbed prêt - Dimension: {self.dimension}D")
        print(f"⚠️ AUDIT: FastEmbed utilisé (pas de Hugging Face/SentenceTransformers)")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding pour un texte unique
        
        Args:
            text: Texte à encoder
            
        Returns:
            Vecteur d'embedding (liste de floats)
        """
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Génère des embeddings pour plusieurs textes (batch)
        Plus efficace que des appels individuels
        
        Args:
            texts: Liste de textes à encoder
            
        Returns:
            Liste de vecteurs d'embeddings
        """
        embeddings = list(self.model.embed(texts))
        return [emb.tolist() for emb in embeddings]
    
    def create_product_text(self, name: str, description: str, category: str = "") -> str:
        """
        Crée un texte optimisé pour l'embedding d'un produit
        
        Format: "category | name | description"
        
        Args:
            name: Nom du produit
            description: Description du produit
            category: Catégorie du produit (optionnel)
            
        Returns:
            Texte formaté pour l'embedding
        """
        parts = []
        if category:
            parts.append(category)
        parts.append(name)
        if description:
            parts.append(description)
        return " | ".join(parts)
    
    def get_dimension(self) -> int:
        """Retourne la dimension des embeddings"""
        return self.dimension
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs
        
        Args:
            vec1: Premier vecteur
            vec2: Deuxième vecteur
            
        Returns:
            Score de similarité (0.0 à 1.0)
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
