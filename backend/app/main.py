import os
import httpx

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import ai, auth, clients, norms, parts

app = FastAPI(title="Cost Sheet Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
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
app.include_router(auth.router)


@app.middleware("http")
async def require_costsheet_login(request: Request, call_next):
    """Require a current Cost Sheet customer session for application APIs and uploads."""
    path = request.url.path
    if request.method == "OPTIONS" or path == "/health" or path == "/api/auth/login":
        return await call_next(request)
    if not (path.startswith("/api/") or path.startswith("/static/")):
        return await call_next(request)

    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return JSONResponse({"detail": "Please sign in to use Cost Sheet."}, status_code=401)

    if request.method in {"GET", "HEAD", "OPTIONS"} or path in {
        "/api/v1/calculate",
    } or path.endswith("/ai-insights") or path == "/api/auth/change-password":
        required_permission = "read"
    elif request.method == "DELETE":
        required_permission = "delete"
    else:
        required_permission = "write"

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(
                f"{settings.auth_api_url.rstrip('/')}/api/auth/me",
                params={"product_code": "costsheet", "required_permission": required_permission},
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError:
        return JSONResponse(
            {"detail": "The sign-in service is temporarily unavailable. Please try again."},
            status_code=503,
        )

    if response.status_code != 200:
        try:
            detail = response.json().get("detail", "Your session is no longer valid. Please sign in again.")
        except ValueError:
            detail = "Your session is no longer valid. Please sign in again."
        return JSONResponse({"detail": detail}, status_code=response.status_code)

    request.state.costsheet_user = response.json()
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}
