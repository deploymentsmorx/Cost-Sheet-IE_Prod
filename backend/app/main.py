from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai, clients, norms, parts

app = FastAPI(title="Cost Sheet Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router)
app.include_router(norms.router)
app.include_router(parts.router)
app.include_router(ai.router)


@app.get("/health")
def health():
    return {"status": "ok"}
