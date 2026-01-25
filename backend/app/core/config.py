from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "FinCommerce Platform"
    DEBUG: bool = True
    
    # Qdrant Cloud
    QDRANT_URL: str = "https://your-cluster.qdrant.io"
    QDRANT_API_KEY: str = ""
    
    # Groq AI (Fast inference) - FREE
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Updated model
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    
    # Google Gemini (Vision OCR) - FREE
    GEMINI_API_KEY: str = ""  # Get at https://makersuite.google.com/app/apikey
    
    # Hugging Face (FREE backup VLM)
    HUGGINGFACE_API_KEY: str = ""  # Optional, works without it
    
    # Collections
    COLLECTION_SUPERMARKET: str = "products_supermarket"
    
    # Embedding (SigLIP for images only)
    CLIP_DIMENSION: int = 768  # SigLIP base produces 768-dimensional embeddings
    
    # MMR Configuration
    MMR_DIVERSITY_SCORE: float = 0.5
    
    # Database (SQLite3 - built into Python)
    DATABASE_PATH: str = "./fincommerce.db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """CORS allowed origins"""
        return ["http://localhost:3000", "http://localhost:5173"]

settings = Settings()
