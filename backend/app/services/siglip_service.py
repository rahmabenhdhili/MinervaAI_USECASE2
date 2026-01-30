from transformers import AutoModel, AutoImageProcessor
from PIL import Image, ImageEnhance, ImageOps
import torch
from typing import List
import io

class SigLIPService:
    """
    SigLIP service for image embeddings in Shopping Mode.
    Uses Google's SigLIP (Sigmoid Loss for Language-Image Pre-training).
    SigLIP is more efficient and often more accurate than CLIP.
    Enhanced with image preprocessing for better recognition.
    """
    
    def __init__(self):
        # Use base model (fine-tuned requires 8GB+ page file - see FIX_MEMORY_ERROR.md)
        self.model_name = "google/siglip-base-patch16-224"
        print(f"[LOADING] SigLIP base model from {self.model_name}...")
        
        # Load model and image processor (SigLIP is vision-only, no tokenizer needed)
        try:
            self.model = AutoModel.from_pretrained(self.model_name)
            self.image_processor = AutoImageProcessor.from_pretrained(self.model_name)
            print("[OK] SigLIP model and processor loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load SigLIP: {e}")
            raise
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()
        print(f"[OK] SigLIP base model loaded on {self.device}")
        print(f"[INFO] To use fine-tuned model: Increase Windows page file (see FIX_MEMORY_ERROR.md)")
    
    def embed_image(self, image_bytes: bytes, preprocess: bool = True) -> List[float]:
        """
        Generate embedding for an image with optional preprocessing
        
        Args:
            image_bytes: Raw image bytes
            preprocess: Whether to apply image enhancements (default: True)
            
        Returns:
            768-dimensional embedding vector (SigLIP base)
        """
        try:
            # Load and preprocess image
            if preprocess:
                image = self._preprocess_image(image_bytes)
            else:
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Process image for SigLIP using image processor
            inputs = self.image_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
                
                # For SigLIP, the output should be a tensor directly
                # If it's a model output object, get the pooler_output or last_hidden_state
                if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                    image_features = outputs.pooler_output
                elif hasattr(outputs, 'last_hidden_state'):
                    # Take the mean of the last hidden state (global average pooling)
                    image_features = outputs.last_hidden_state.mean(dim=1)
                elif torch.is_tensor(outputs):
                    image_features = outputs
                else:
                    # Fallback - try to access the tensor
                    image_features = outputs[0] if hasattr(outputs, '__getitem__') else outputs
                
                # Normalize for cosine similarity
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy()[0].tolist()
        
        except Exception as e:
            print(f"[ERROR] Error embedding image: {e}")
            raise
    
    def _preprocess_image(self, image_bytes: bytes) -> Image.Image:
        """
        Preprocess image for better recognition
        
        Enhancements:
        - Auto-rotation based on EXIF
        - Contrast enhancement
        - Sharpness enhancement
        - Center cropping
        """
        try:
            # Load image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Auto-rotate based on EXIF data (fixes phone photos)
            img = ImageOps.exif_transpose(img)
            
            # Enhance contrast (makes products stand out)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)  # 30% more contrast
            
            # Enhance sharpness (clearer details)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)  # 20% sharper
            
            # Enhance color saturation (more vibrant)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)  # 10% more color
            
            # Center crop to focus on product (removes background noise)
            img = self._center_crop(img, crop_ratio=0.9)
            
            return img
            
        except Exception as e:
            print(f"[WARNING] Preprocessing failed, using original image: {e}")
            # Fallback to original
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    def _center_crop(self, img: Image.Image, crop_ratio: float = 0.9) -> Image.Image:
        """
        Center crop image to focus on product
        
        Args:
            img: PIL Image
            crop_ratio: Ratio of image to keep (0.9 = keep 90% of center)
            
        Returns:
            Cropped image
        """
        width, height = img.size
        
        # Calculate crop size
        crop_width = int(width * crop_ratio)
        crop_height = int(height * crop_ratio)
        
        # Calculate crop box (centered)
        left = (width - crop_width) // 2
        top = (height - crop_height) // 2
        right = left + crop_width
        bottom = top + crop_height
        
        return img.crop((left, top, right, bottom))
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text (for cross-modal search)"""
        try:
            inputs = self.tokenizer(text=[text], return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.get_text_features(**inputs)
                # Normalize
                text_features = outputs / outputs.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy()[0].tolist()
        
        except Exception as e:
            print(f"[ERROR] Error embedding text: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of SigLIP embeddings"""
        return 768  # SigLIP base produces 768-dimensional embeddings

# Singleton instance - lazy initialization
siglip_service = None

def get_siglip_service():
    """Get or create SigLIP service instance"""
    global siglip_service
    if siglip_service is None:
        siglip_service = SigLIPService()
    return siglip_service
