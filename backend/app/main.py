from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="DevOs API",
    description="Backend API for the DevOs platform",
    version="0.1.0",
    debug=settings.DEBUG,
)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns the current health status of the API."""
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "debug": settings.DEBUG,
    }


# ── Root ──────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the DevOs API 🚀"}
