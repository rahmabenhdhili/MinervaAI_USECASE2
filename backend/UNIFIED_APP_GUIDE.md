# 🚀 Unified MinervaAI Platform Guide

## Overview

The **Unified MinervaAI Platform** combines all separate applications into a single FastAPI server with organized API prefixes.

### Previous Structure (Separate Apps)
- `main.py` - B2C Marketplace (Port 8000)
- `mainB2B.py` - B2B Supplier Search (Port 8000)
- `main_usershop.py` - Usershop Recommendations (Port 8000)
- `app/main_shopgpt.py` - ShopGPT Image Search (Port 8000)

**Problem**: Only one app could run at a time on port 8000.

### New Structure (Unified App)
- `main_unified.py` - **ALL APPS IN ONE** (Port 8000)
  - `/api/b2c/*` - B2C Marketplace endpoints
  - `/api/b2b/*` - B2B Supplier Search endpoints
  - `/api/usershop/*` - Usershop Recommendations endpoints
  - `/api/shopgpt/*` - ShopGPT Image Search endpoints

**Solution**: All services run simultaneously on the same port with different prefixes.

---

## 🎯 Services Included

### 1. B2C Marketplace (`/api/b2c/*`)
**Purpose**: E-commerce platform with real-time product scraping and marketplace management

**Key Features**:
- Real-time product scraping (Amazon, Alibaba, Walmart, Cdiscount)
- Semantic search with Qdrant + FastEmbed
- AI recommendations with Groq LLM
- User marketplace management
- Order tracking with profit calculations
- Marketing strategy generation

**Main Endpoints**:
```
POST   /api/b2c/recommend              - Get AI recommendations
POST   /api/b2c/search/semantic        - Real-time semantic search
POST   /api/b2c/marketing              - Generate marketing strategy
GET    /api/b2c/marketplace/products   - List marketplace products
POST   /api/b2c/marketplace/products   - Add product to marketplace
GET    /api/b2c/orders                 - List orders
POST   /api/b2c/orders                 - Create order
GET    /api/b2c/settings               - Get marketplace settings
```

---

### 2. B2B Supplier Search (`/api/b2b/*`)
**Purpose**: Business-to-business supplier search with personalization

**Key Features**:
- Supplier semantic search
- Price optimization by quantity
- User authentication (JWT)
- Search/click tracking for personalization
- AI explanations for supplier recommendations

**Main Endpoints**:
```
POST   /api/b2b/auth/signup            - User registration
POST   /api/b2b/auth/login             - User login (JWT)
POST   /api/b2b/search                 - Search suppliers (requires auth)
POST   /api/b2b/click                  - Track user clicks (requires auth)
```

**Note**: B2B endpoints require JWT authentication. Get token from `/api/b2b/auth/login` and include in headers:
```
Authorization: Bearer <your_token>
```

---

### 3. Usershop Recommendations (`/api/usershop/*`)
**Purpose**: CSV-based product recommendation system with advanced filtering

**Key Features**:
- CSV bulk product import
- Advanced multi-factor scoring (vector + keywords + price)
- Price range filtering
- Product comparison with AI
- Automatic deduplication
- Sort by relevance or price

**Main Endpoints**:
```
POST   /api/usershop/recommend         - Get recommendations with filters
POST   /api/usershop/compare           - Compare two products
GET    /api/usershop/product/{id}      - Get product details
POST   /api/usershop/search            - Simple text search
POST   /api/usershop/add-products      - Upload CSV file
POST   /api/usershop/load-from-directory - Load all CSVs from folder
GET    /api/usershop/stats             - Database statistics
```

---

### 4. ShopGPT Image Search (`/api/shopgpt/*`)
**Purpose**: Image-based product search with AI vision models

**Key Features**:
- Image-based product search
- OCR text extraction
- Image captioning
- Visual similarity search
- Virtual cart management

**Main Endpoints**:
```
GET    /api/shopgpt/info               - Service information
(Additional endpoints from shopping router)
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create or update `.env` file:
```env
# Qdrant Cloud
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_api_key
QDRANT_COLLECTION_B2BPREMIUM=minerva_b2b
QDRANT_COLLECTION_USERSHOP=minerva_usershop

# Groq API
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# MongoDB (for B2B)
MONGO_URI=mongodb://localhost:27017

# Scraping APIs
SCRAPERAPI_KEY_AMAZON=your_amazon_key
SCRAPERAPI_KEY_ALIBABA=your_alibaba_key
FIRECRAWL_API_KEY_WALMART=your_walmart_key
FIRECRAWL_API_KEY_CDISCOUNT=your_cdiscount_key

# JWT Secret (for B2B)
SECRET_KEY=your_secret_key
```

### 3. Run Unified Server
```bash
python main_unified.py
```

### 4. Access Services
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📊 API Usage Examples

### B2C: Search Products
```bash
curl -X POST "http://localhost:8000/api/b2c/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "gaming laptop",
    "use_amazon": true,
    "use_alibaba": true,
    "max_results": 20
  }'
```

### B2B: Search Suppliers (with auth)
```bash
# 1. Login
curl -X POST "http://localhost:8000/api/b2b/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# 2. Search (use token from login)
curl -X POST "http://localhost:8000/api/b2b/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "product_name": "office chairs",
    "quantity": 100,
    "max_price": 5000
  }'
```

### Usershop: Get Recommendations
```bash
curl -X POST "http://localhost:8000/api/usershop/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "laptop",
    "category": "electronics",
    "min_price": 500,
    "max_price": 1500,
    "sort_by": "price_asc",
    "limit": 10
  }'
```

### Usershop: Compare Products
```bash
curl -X POST "http://localhost:8000/api/usershop/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id_1": "uuid-1",
    "product_id_2": "uuid-2"
  }'
```

---

## 🔧 Architecture

### Service Initialization Flow
```
1. Lifespan startup triggered
   ↓
2. Initialize B2C services
   - RecommendationService
   - RealtimeSemanticSearchService
   - MarketplaceService
   - OrderService
   - SettingsService
   ↓
3. Initialize B2B services (if available)
   - EmbeddingAgent
   - SemanticSearchAgent
   - PriceOptimizer
   - GroqExplainer
   ↓
4. Initialize Usershop services
   - Qdrant collection
   - Auto-load products from /data
   ↓
5. Initialize ShopGPT (if available)
   - Include shopping router
   ↓
6. Server ready - all services active
```

### Data Storage
- **B2C Marketplace**: JSON files (`marketplace_products.json`, `orders.json`)
- **B2B**: MongoDB (user data, events)
- **Usershop**: Qdrant Cloud (product vectors)
- **ShopGPT**: SQLite + Qdrant Cloud

### AI Models Used
- **Embeddings**: FastEmbed (BAAI/bge-small-en-v1.5) - 384 dimensions
- **LLM**: Groq (Llama 3.3 70B) - Intent analysis, recommendations, comparisons
- **Vision** (ShopGPT): SigLIP, TrOCR, BLIP

---

## 🎯 Migration Guide

### From Separate Apps to Unified

**Before** (running separate apps):
```bash
# Only one could run at a time
python main.py              # B2C on port 8000
python mainB2B.py           # B2B on port 8000 (conflicts!)
python main_usershop.py     # Usershop on port 8000 (conflicts!)
```

**After** (unified app):
```bash
# All services run together
python main_unified.py      # Everything on port 8000
```

### Update Frontend API Calls

**Before**:
```javascript
// B2C
fetch('http://localhost:8000/api/recommend', ...)

// B2B
fetch('http://localhost:8000/search', ...)

// Usershop
fetch('http://localhost:8000/recommend', ...)
```

**After**:
```javascript
// B2C
fetch('http://localhost:8000/api/b2c/recommend', ...)

// B2B
fetch('http://localhost:8000/api/b2b/search', ...)

// Usershop
fetch('http://localhost:8000/api/usershop/recommend', ...)
```

---

## 🐛 Troubleshooting

### B2B Endpoints Not Available
**Issue**: B2B scripts not found
**Solution**: Check if `scripts/` folder exists with B2B files:
- `embedding_agent_B2B.py`
- `qroq_explainerB2B.py`
- `search_B2B.py`
- `price_optimizeB2B.py`

### ShopGPT Endpoints Not Available
**Issue**: ShopGPT modules not found
**Solution**: Check if `app/api/shopping.py` and `app/core/config.py` exist

### Usershop Products Not Loading
**Issue**: No products in Qdrant
**Solution**: 
1. Create `/data` folder in backend
2. Add CSV files with columns: `url, name, category, brand, img, description, price`
3. Restart server (auto-loads on startup)
4. Or manually load: `POST /api/usershop/load-from-directory`

### Port Already in Use
**Issue**: Port 8000 is occupied
**Solution**: 
1. Stop old main.py/mainB2B.py/main_usershop.py processes
2. Or change port in `main_unified.py` (line with `uvicorn.run`)

---

## 📈 Performance Tips

1. **Parallel Scraping**: B2C uses `asyncio.gather()` for simultaneous scraping
2. **Batch Embeddings**: FastEmbed processes multiple texts at once
3. **Qdrant :memory:**: Real-time search uses ephemeral collections (faster)
4. **Connection Pooling**: Reuse Qdrant/MongoDB connections

---

## 🔐 Security Notes

### B2B Authentication
- Uses JWT tokens
- Token expires after configured time
- Include token in `Authorization: Bearer <token>` header

### API Keys
- Store in `.env` file (never commit)
- Use different keys for each scraping service
- Rotate keys regularly

---

## 📝 Development

### Adding New Endpoints
```python
# Add to main_unified.py

@app.post("/api/b2c/new-endpoint")
async def b2c_new_feature():
    """B2C: New feature description"""
    # Your code here
    return {"status": "success"}
```

### Testing Individual Services
```python
# Test B2C only
if __name__ == "__main__":
    # Comment out B2B/Usershop initialization in lifespan()
    uvicorn.run("main_unified:app", ...)
```

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **Groq API**: https://console.groq.com/docs
- **FastEmbed**: https://qdrant.github.io/fastembed/

---

## 🎉 Summary

The unified platform provides:
- ✅ All services in one server
- ✅ Organized API structure with prefixes
- ✅ No port conflicts
- ✅ Shared resources (Qdrant, Groq)
- ✅ Easy deployment
- ✅ Comprehensive API documentation

**Start the server and access all services at once!**

```bash
python main_unified.py
```

Visit http://localhost:8000/docs to explore all endpoints interactively.
