from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration centralisée de l'application"""
    
    # Groq API
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Qdrant Cloud
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_b2bpremium: str = "minerva_b2b_premium"
    qdrant_collection_usershop: str = "minerva_usershop"
    
    # Backward compatibility
    collection_name: str = "minerva_products_test"  # Old collection name
    
    # Embedding Model (FastEmbed)
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    
    # Bright Data MCP (Optionnel - Free Tier ne nécessite que l'API Key)
    bright_data_api_key: str = ""
    
    # ScraperAPI - Clés séparées pour chaque site
    scraperapi_key_amazon: str = ""      # Clé dédiée Amazon
    scraperapi_key_alibaba: str = ""     # Clé dédiée Alibaba
    scraperapi_key: str = ""             # Clé par défaut (backward compatibility)
    
    # Firecrawl API - Clés séparées pour chaque site
    firecrawl_api_key_walmart: str = ""   # Clé dédiée Walmart
    firecrawl_api_key_cdiscount: str = "" # Clé dédiée Cdiscount
    firecrawl_api_key: str = ""           # Clé par défaut (backward compatibility)
    
    # Apify (Optionnel - $5 free credit)
    apify_api_token: str = ""
    
    # API Configuration
    api_title: str = "AI Product Recommendation System"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """Singleton pour les settings"""
    return Settings()
