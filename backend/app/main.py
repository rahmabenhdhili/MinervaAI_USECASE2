from fastapi import FastAPI

app = FastAPI(title="MinervaAI Backend")


@app.get("/minerva")
def minerva_info():
    return {"message": "MinervaAI Backend is ready!"}

