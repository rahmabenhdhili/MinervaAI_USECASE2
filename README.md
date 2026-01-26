# Dinero

## Description

Dinero is a next-generation shopping platform that combines semantic product search with real-time financial context to deliver personalized, budget-aware recommendations.  
Instead of relying on basic keyword search, Dinero understands user intent using vector embeddings and retrieves the most relevant suppliers and products while considering affordability.

The platform helps users not only find what they want, but also what they can truly afford, enabling smarter and more responsible purchasing decisions.

---

## Key Features

- Semantic supplier and product search using vector similarity
- Budget-aware recommendations
- Recommendations system based on previous searches and interaction history
- Intelligent data pipeline (CSV ingestion → embeddings → vector database)
- Fast and scalable search with Qdrant
- Clean and modern frontend interface
- Modular backend architecture ready for AI agents

---

## Tech Stack

### Backend
- Python
- FastAPI
- Qdrant (Vector Database)
- FastEmbed (Text embeddings – BGE model)
- SQLite (Product metadata storage
- Crawl4ai (Web scraping)
- Groq (Ultra-fast LLM inference (Llama 3.3 70B))
- Pytesseract (OCR for text extraction)
- SigLIP (Visual embeddings (Google's vision-language model))

### Frontend
- React 18 - UI framework
- Vite - Build tool
- Axios - HTTP client
- Tailwind CSS - Styling


### AI & Data
- SigLIP (google/siglip-base-patch16-224) - 768-dim visual embeddings
- FastEmbed (BAAI/bge-small-en-v1.5) - 384-dim text embeddings
- Groq API - LLM inference
- Pytesseract - OCR engine

---

## Setup & Run Instructions

### 1. Clone the repository
```bash
git clone 
cd MinervaAI_USECASE2
```
### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
### 3. Set Environment Variables
```bash
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_api_key
```
### 4. Run the Backend
```bash
uvicorn main:app --reload
```
### 5. Frontend Setup
```bash
cd frontend
npm install
npm start
```
## Contributors
- [Mariem Jlassi](https://github.com/Maryem-Jlassi)
- [Wassim Guesmi](https://github.com/zaatar1x)
- [Rahma Ben Hedhili](https://github.com/rahmabenhdhili)
- [Islem Labidi](https://github.com/islemlabidi0)  

*Making smart shopping accessible for everyone*



