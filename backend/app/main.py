import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import ai, clients, norms, parts

app = FastAPI(title="Cost Sheet Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(os.path.join(_static_dir, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

app.include_router(clients.router)
app.include_router(norms.router)
app.include_router(parts.router)
app.include_router(ai.router)


@app.get("/health")
def health():
    return {"status": "ok"}
