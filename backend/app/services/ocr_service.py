"""
OCR Service using Pytesseract for text extraction from product images.
"""
import pytesseract
from PIL import Image
from io import BytesIO
from typing import List, Dict, Optional
import re


class OCRService:
    """
    OCR service using Pytesseract for extracting text from product images.
    """
    
    def __init__(self):
        """Initialize OCR service"""
        # Configure pytesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def get_text_only(
        self, 
        image_bytes: bytes, 
        min_confidence: float = 0.3,
        lang: str = 'eng+fra+ara'
    ) -> List[str]:
        """
        Extract text from image using Pytesseract.
        
        Args:
            image_bytes: Raw image bytes
            min_confidence: Minimum confidence threshold (0-1)
            lang: Languages to detect (eng+fra+ara for English, French, Arabic)
            
        Returns:
            List of extracted text strings
        """
        try:
            # Load image
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(
                image, 
                lang=lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Filter by confidence
            texts = []
            for i, conf in enumerate(data['conf']):
                if conf != -1 and float(conf) / 100 >= min_confidence:
                    text = data['text'][i].strip()
                    if text:
                        texts.append(text)
            
            return texts
        
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return []
    
    def extract_brand_and_product(self, image_bytes: bytes) -> Dict[str, Optional[str]]:
        """
        Extract brand and product name from image.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with 'brand' and 'product' keys
        """
        texts = self.get_text_only(image_bytes, min_confidence=0.5)
        
        if not texts:
            return {"brand": None, "product": None}
        
        # Common brand names (Tunisia market)
        known_brands = [
            'danone', 'delice', 'vitalait', 'president', 'yoplait',
            'nestle', 'coca-cola', 'pepsi', 'fanta', 'sprite',
            'safia', 'ain', 'baraka', 'cristal', 'melliti'
        ]
        
        brand = None
        product_parts = []
        
        for text in texts:
            text_lower = text.lower()
            
            # Check if it's a known brand
            if not brand:
                for known_brand in known_brands:
                    if known_brand in text_lower:
                        brand = text
                        break
            
            # Collect product info (skip very short words)
            if len(text) > 2:
                product_parts.append(text)
        
        product = " ".join(product_parts[:5]) if product_parts else None
        
        return {
            "brand": brand,
            "product": product
        }
    
    def get_search_hint(self, image_bytes: bytes) -> str:
        """
        Get a search hint from image text (brand + product keywords).
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Search hint string
        """
        extracted = self.extract_brand_and_product(image_bytes)
        
        parts = []
        if extracted['brand']:
            parts.append(extracted['brand'])
        if extracted['product']:
            # Take first few words only
            product_words = extracted['product'].split()[:3]
            parts.extend(product_words)
        
        return " ".join(parts) if parts else ""
    
    def extract_text_simple(self, image_bytes: bytes, lang: str = 'eng+fra+ara') -> str:
        """
        Simple text extraction without confidence filtering.
        
        Args:
            image_bytes: Raw image bytes
            lang: Languages to detect
            
        Returns:
            Extracted text as single string
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            text = pytesseract.image_to_string(image, lang=lang)
            return text.strip()
        
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""


# Singleton instance
_ocr_service = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service instance (lazy initialization)"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
