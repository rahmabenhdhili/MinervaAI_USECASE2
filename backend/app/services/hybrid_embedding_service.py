"""
Hybrid Embedding Service - Visual search with SigLIP embeddings and OCR.

This service creates embeddings using:
1. Visual embeddings from SigLIP (primary signal)
2. OCR text extraction for keywords (brand, product type)
"""
from typing import Dict, Any, Optional, List
from app.services.siglip_service import siglip_service
from app.services.ocr_service import get_ocr_service
import numpy as np


class HybridEmbeddingService:
    """
    Embedding service using SigLIP for visual embeddings + Pytesseract OCR.
    """
    
    def __init__(self):
        self.use_ocr = True  # Enable OCR by default
    
    def create_query_embedding(
        self,
        image_bytes: bytes,
        ocr_text: Optional[str] = None,
        use_vlm: bool = True
    ) -> Dict[str, Any]:
        """
        Create embedding for a query image with OCR keyword extraction.
        
        Args:
            image_bytes: Raw image bytes
            ocr_text: Pre-extracted OCR text (optional)
            use_vlm: Whether to use OCR (renamed for compatibility)
            
        Returns:
            Dictionary with:
            - embedding: Visual embedding vector
            - ocr_text: Extracted text from image
            - vlm_caption: Same as ocr_text (for compatibility)
            - combined_text: Extracted keywords
            - detected_category: Detected category from keywords
        """
        # Generate visual embedding (SigLIP)
        visual_embedding = siglip_service.embed_image(image_bytes, preprocess=True)
        
        # Extract text using OCR
        extracted_text = ""
        detected_category = None
        
        if use_vlm and self.use_ocr:
            if not ocr_text:
                try:
                    ocr_service = get_ocr_service()
                    extracted_text = ocr_service.get_search_hint(image_bytes)
                    
                    if extracted_text:
                        print(f"  📝 OCR: {extracted_text}")
                        # Detect category from extracted text
                        detected_category = self._detect_category(extracted_text)
                        if detected_category:
                            print(f"  🏷️ Category: {detected_category}")
                except Exception as e:
                    print(f"  ⚠️ OCR failed: {e}")
            else:
                extracted_text = ocr_text
        
        return {
            "embedding": visual_embedding,
            "ocr_text": extracted_text,
            "vlm_caption": extracted_text,  # For compatibility
            "combined_text": extracted_text,
            "detected_category": detected_category
        }
    
    def _detect_category(self, text: str) -> Optional[str]:
        """
        Detect product category from OCR text.
        
        Args:
            text: Extracted OCR text
            
        Returns:
            Detected category or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Category keywords (Arabic, French, English)
        categories = {
            "yogurt": ["yaourt", "yogurt", "yoghurt", "danone", "delice", "yab"],
            "milk": ["lait", "milk", "lben", "vitalait", "delice"],
            "cheese": ["fromage", "cheese", "jben", "president"],
            "juice": ["jus", "juice", "nectar"],
            "water": ["eau", "water", "safia", "ain"],
            "shampoo": ["shampoo", "shampoing", "shampooing"],
            "soap": ["savon", "soap", "صابون"],
            "oil": ["huile", "oil", "زيت"],
            "biscuit": ["biscuit", "gâteau", "cake", "cookie"],
            "beverage": ["boisson", "drink", "soda"],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return None
    
    def create_product_embedding(
        self,
        image_bytes: Optional[bytes] = None,
        product_text: Optional[str] = None
    ) -> List[float]:
        """
        Create embedding for a product (pure visual).
        
        Args:
            image_bytes: Product image bytes (required)
            product_text: Ignored (for compatibility)
            
        Returns:
            Visual embedding vector
        """
        if image_bytes:
            return siglip_service.embed_image(image_bytes, preprocess=True)
        else:
            # Return zero vector if no image
            return [0.0] * 768
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of hybrid embeddings"""
        return 768  # SigLIP dimension


# Singleton instance
hybrid_embedding_service = HybridEmbeddingService()
