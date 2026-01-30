from fastapi import FastAPI
from app.routes import auth, events

app = FastAPI(title="MinervaAI Backend")  # Keep your team’s title

# Include auth routes
app.include_router(auth.router)

# Existing “minerva” endpoint
@app.get("/minerva")
def minerva_info():
    return {"message": "MinervaAI Backend is ready!"}

# Optional health check
@app.get("/ping")
async def ping():
    return {"status": "ok"}

# Include event tracking routes
app.include_router(events.router)