from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import shopping

app = FastAPI(
    title="Smart Shopping Assistant",
    description="AI-powered real-time shopping with image recognition and price comparison",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shopping.router)

@app.get("/")
async def root():
    return {
        "message": "Smart Shopping Assistant API",
        "version": "3.0.0",
        "mode": "Real-time Shopping (Image-based)",
        "architecture": {
            "ai_models": {
                "image_embedding": "SigLIP (Google)",
                "ocr": "TrOCR (Microsoft)",
                "captioning": "BLIP (Salesforce)",
                "llm": "Groq (Llama 3.3 70B)"
            },
            "vector_db": "Qdrant Cloud",
            "storage": "SQLite + Qdrant"
        },
        "features": [
            "Image-based product search",
            "Real-time price comparison",
            "Multi-market support",
            "Virtual cart with budget tracking",
            "AI-powered recommendations",
            "Cheaper alternatives finder"
        ],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "components": {
            "groq": "enabled" if settings.GROQ_API_KEY else "missing_key",
            "qdrant": "cloud",
            "siglip": "enabled",
            "trocr": "enabled",
            "blip": "enabled"
        }
    }

