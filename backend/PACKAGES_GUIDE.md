# 📦 Package Dependencies Guide

## Overview

This document explains all packages used in the MinervaAI Unified Platform and their purposes.

---

## 🎯 Core Framework

### FastAPI (>=0.104.0)
**Purpose**: Modern, fast web framework for building APIs  
**Used by**: All services (main framework)  
**Features**:
- Automatic API documentation
- Data validation with Pydantic
- Async/await support
- High performance

### Uvicorn (>=0.24.0)
**Purpose**: ASGI server for running FastAPI  
**Used by**: Server startup  
**Features**:
- Lightning-fast ASGI server
- Auto-reload in development
- Production-ready

### python-multipart (>=0.0.6)
**Purpose**: Handle file uploads  
**Used by**: Usershop CSV upload (`/api/usershop/add-products`)  
**Features**:
- Form data parsing
- File upload handling

---

## 🗄️ Database

### qdrant-client (>=1.7.0)
**Purpose**: Vector database client  
**Used by**: All services for semantic search  
**Features**:
- Vector similarity search
- Cloud and local support
- High-performance indexing

**Collections**:
- `minerva_b2b_premium` - B2C & B2B products
- `minerva_usershop` - Usershop products
- `temp_search_*` - Ephemeral real-time search

### motor (>=3.3.0)
**Purpose**: Async MongoDB driver  
**Used by**: B2B service for user data and events  
**Features**:
- Async/await support
- Full MongoDB functionality
- Connection pooling

**Collections**:
- `users` - User accounts
- `events` - Search/click tracking

---

## 🤖 AI/ML

### fastembed (>=0.2.0)
**Purpose**: Fast text embeddings (Qdrant-compatible)  
**Used by**: B2C, B2B, Usershop for vector embeddings  
**Model**: BAAI/bge-small-en-v1.5 (384 dimensions)  
**Features**:
- Optimized for Qdrant
- Batch processing
- Low memory footprint

**Why not sentence-transformers?**
- FastEmbed is faster and lighter
- Better Qdrant integration
- No CUDA dependencies

### groq (>=0.4.0)
**Purpose**: Ultra-fast LLM inference  
**Used by**: All services for AI generation  
**Model**: Llama 3.3 70B Versatile  
**Features**:
- Extremely fast inference
- High-quality responses
- Cost-effective

**Use cases**:
- B2C: Intent analysis, recommendations, marketing
- B2B: Supplier explanations
- Usershop: Product descriptions, comparisons

### transformers (>=4.35.0) [OPTIONAL]
**Purpose**: Hugging Face transformers library  
**Used by**: ShopGPT (if using custom models)  
**Note**: Can be removed if only using FastEmbed

### torch (>=2.1.0) [OPTIONAL]
**Purpose**: PyTorch deep learning framework  
**Used by**: Transformers backend  
**Note**: Large package (~2GB), optional if not using custom models

### sentence-transformers (>=2.2.0) [OPTIONAL]
**Purpose**: Sentence embeddings  
**Used by**: Alternative to FastEmbed  
**Note**: Heavier than FastEmbed, kept for compatibility

---

## 🌐 Web Scraping

### httpx (>=0.25.0)
**Purpose**: Modern async HTTP client  
**Used by**: Amazon, Alibaba scrapers  
**Features**:
- Async/await support
- HTTP/2 support
- Connection pooling

**Why not requests?**
- Async support (non-blocking)
- Better performance
- Modern API

### requests (>=2.31.0)
**Purpose**: Simple HTTP library  
**Used by**: Sync HTTP calls (fallback)  
**Features**:
- Simple API
- Wide compatibility
- Stable

### beautifulsoup4 (>=4.12.0)
**Purpose**: HTML/XML parsing  
**Used by**: Amazon, Alibaba scrapers  
**Features**:
- Easy HTML navigation
- Robust parsing
- Multiple parsers support

### lxml (>=4.9.0)
**Purpose**: Fast XML/HTML parser  
**Used by**: BeautifulSoup backend  
**Features**:
- Fastest parser
- XPath support
- Memory efficient

### crawl4ai (>=0.3.0)
**Purpose**: AI-powered web crawler  
**Used by**: Advanced scraping scenarios  
**Features**:
- AI-driven extraction
- JavaScript rendering
- Smart content detection

### selenium (>=4.15.0)
**Purpose**: Browser automation  
**Used by**: Dynamic content scraping  
**Features**:
- Full browser control
- JavaScript execution
- Screenshot capture

**Note**: Requires browser driver (ChromeDriver, GeckoDriver)

### firecrawl-py (>=0.0.5)
**Purpose**: Firecrawl API client  
**Used by**: Walmart, Cdiscount scrapers  
**Features**:
- AI-powered extraction
- No browser needed
- Clean structured data

**API Keys Required**:
- `FIRECRAWL_API_KEY_WALMART`
- `FIRECRAWL_API_KEY_CDISCOUNT`

---

## 🖼️ Image Processing

### Pillow (>=10.0.0)
**Purpose**: Image manipulation  
**Used by**: ShopGPT, image processing  
**Features**:
- Image resizing
- Format conversion
- Filters and effects

### pytesseract (>=0.3.10)
**Purpose**: OCR (Optical Character Recognition)  
**Used by**: ShopGPT for text extraction from images  
**Features**:
- Text extraction
- Multiple languages
- Layout analysis

**Note**: Requires Tesseract OCR engine installed on system

---

## 🔐 Authentication & Security

### python-jose[cryptography] (>=3.3.0)
**Purpose**: JWT token handling  
**Used by**: B2B authentication  
**Features**:
- JWT encoding/decoding
- Token validation
- Cryptographic signing

### passlib[bcrypt] (>=1.7.4)
**Purpose**: Password hashing  
**Used by**: B2B user authentication  
**Features**:
- Secure password hashing
- Multiple algorithms
- Salt generation

### bcrypt (>=4.0.0)
**Purpose**: Bcrypt hashing algorithm  
**Used by**: Passlib backend  
**Features**:
- Slow hashing (security)
- Adaptive cost factor
- Industry standard

---

## 📊 Data Processing

### pandas (>=2.0.0)
**Purpose**: Data manipulation and analysis  
**Used by**: Usershop CSV loading  
**Features**:
- CSV reading/writing
- Data cleaning
- DataFrame operations

**Use cases**:
- Load products from CSV
- Data validation
- Deduplication

### numpy (>=1.24.0)
**Purpose**: Numerical computing  
**Used by**: Vector operations, embeddings  
**Features**:
- Array operations
- Mathematical functions
- Linear algebra

---

## 🛠️ Utilities

### python-dotenv (>=1.0.0)
**Purpose**: Load environment variables from .env  
**Used by**: All services for configuration  
**Features**:
- .env file parsing
- Environment variable management
- Development/production separation

### pydantic (>=2.5.0)
**Purpose**: Data validation and settings  
**Used by**: All services for request/response models  
**Features**:
- Automatic validation
- Type hints
- JSON schema generation

### pydantic-settings (>=2.1.0)
**Purpose**: Settings management  
**Used by**: Configuration classes  
**Features**:
- Environment variable loading
- Settings validation
- Multiple sources

### email-validator (>=2.0.0)
**Purpose**: Email validation  
**Used by**: B2B user registration  
**Features**:
- RFC-compliant validation
- DNS checks
- Syntax validation

---

## 🔧 Optional Dependencies

### redis (>=5.0.0) [COMMENTED OUT]
**Purpose**: In-memory caching  
**Use case**: Cache frequent queries, session storage  
**When to enable**:
- High traffic
- Repeated queries
- Session management

**To enable**:
```bash
pip install redis>=5.0.0
```

### celery (>=5.3.0) [COMMENTED OUT]
**Purpose**: Distributed task queue  
**Use case**: Background jobs, scheduled tasks  
**When to enable**:
- Long-running tasks
- Scheduled scraping
- Email sending

**To enable**:
```bash
pip install celery>=5.3.0
```

---

## 📦 Installation

### Full Installation
```bash
pip install -r requirements.txt
```

### Minimal Installation (Core Only)
```bash
pip install fastapi uvicorn qdrant-client fastembed groq python-dotenv pydantic pydantic-settings
```

### Without Heavy ML Packages
```bash
# Skip torch, transformers, sentence-transformers
pip install -r requirements.txt --no-deps
pip install fastapi uvicorn qdrant-client fastembed groq httpx beautifulsoup4 motor python-jose passlib pandas numpy python-dotenv pydantic pydantic-settings
```

---

## 🎯 Package Usage by Service

### B2C Marketplace
**Required**:
- fastapi, uvicorn
- qdrant-client, fastembed
- groq
- httpx, beautifulsoup4, lxml
- firecrawl-py
- python-dotenv, pydantic

**Optional**:
- crawl4ai, selenium (advanced scraping)

### B2B Supplier Search
**Required**:
- fastapi, uvicorn
- qdrant-client, fastembed
- motor (MongoDB)
- groq
- python-jose, passlib, bcrypt
- python-dotenv, pydantic

### Usershop Recommendations
**Required**:
- fastapi, uvicorn
- qdrant-client, fastembed
- groq
- pandas, numpy
- python-dotenv, pydantic
- python-multipart (CSV upload)

### ShopGPT Image Search
**Required**:
- fastapi, uvicorn
- qdrant-client
- groq
- Pillow, pytesseract
- python-dotenv, pydantic

**Optional**:
- transformers, torch (custom models)

---

## 🔍 Troubleshooting

### Issue: torch installation fails
**Solution**: Install CPU-only version
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: pytesseract not working
**Solution**: Install Tesseract OCR
```bash
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract
```

### Issue: bcrypt compilation error
**Solution**: Install pre-built wheel
```bash
pip install --upgrade pip
pip install bcrypt --only-binary :all:
```

### Issue: lxml installation fails
**Solution**: Install system dependencies
```bash
# Linux: sudo apt-get install libxml2-dev libxslt-dev
# Mac: brew install libxml2
```

### Issue: motor not found
**Solution**: Install motor explicitly
```bash
pip install motor>=3.3.0
```

### Issue: firecrawl-py not found
**Solution**: Install from PyPI
```bash
pip install firecrawl-py>=0.0.5
```

---

## 📊 Package Size Comparison

| Package | Size | Install Time | Required |
|---------|------|--------------|----------|
| fastapi | ~5 MB | Fast | ✅ Yes |
| uvicorn | ~2 MB | Fast | ✅ Yes |
| qdrant-client | ~10 MB | Fast | ✅ Yes |
| fastembed | ~50 MB | Medium | ✅ Yes |
| groq | ~1 MB | Fast | ✅ Yes |
| motor | ~5 MB | Fast | ✅ Yes (B2B) |
| httpx | ~3 MB | Fast | ✅ Yes |
| beautifulsoup4 | ~1 MB | Fast | ✅ Yes |
| pandas | ~30 MB | Medium | ✅ Yes (Usershop) |
| torch | ~2 GB | Slow | ❌ Optional |
| transformers | ~500 MB | Slow | ❌ Optional |
| sentence-transformers | ~100 MB | Medium | ❌ Optional |

**Total (Required)**: ~150 MB  
**Total (With Optional)**: ~3 GB

---

## 🚀 Performance Tips

1. **Skip Optional Packages**: Don't install torch/transformers if not needed
2. **Use FastEmbed**: Faster and lighter than sentence-transformers
3. **Install Pre-built Wheels**: Use `--only-binary :all:` for faster installation
4. **Use Virtual Environment**: Isolate dependencies
5. **Cache Downloads**: Use `pip cache` to speed up reinstalls

---

## 📝 Version Pinning

Current requirements use **minimum versions** (`>=`). For production, consider pinning exact versions:

```bash
# Generate exact versions
pip freeze > requirements-lock.txt
```

**Benefits**:
- Reproducible builds
- No surprise updates
- Easier debugging

**Drawbacks**:
- No security updates
- Manual version management

---

## 🔄 Updating Packages

### Check for updates
```bash
pip list --outdated
```

### Update specific package
```bash
pip install --upgrade package-name
```

### Update all packages
```bash
pip install --upgrade -r requirements.txt
```

### Test after updates
```bash
python main_unified.py
# Check all endpoints work
```

---

## 📚 Additional Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Qdrant**: https://qdrant.tech/documentation/
- **FastEmbed**: https://qdrant.github.io/fastembed/
- **Groq**: https://console.groq.com/docs
- **Motor**: https://motor.readthedocs.io/
- **Pandas**: https://pandas.pydata.org/docs/
- **Firecrawl**: https://www.firecrawl.dev/

---

**Last Updated**: [Current Date]  
**Requirements Version**: 3.0.0
