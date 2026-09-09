from fastapi import FastAPI 

app = FastAPI(title = "Vibe Training Practice API")

@app.get("/health")
def health():
    return {"status": "ok"}