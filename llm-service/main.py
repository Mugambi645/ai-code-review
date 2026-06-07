from fastapi import FastAPI

app = FastAPI(title="LLM Service")

@app.get("/health")
async def health():
    return {"status": "ok"}