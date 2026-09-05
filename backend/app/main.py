import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.repositories import router as repositories_router
from app.api.search import router as search_router
from app.api.chat import router as chat_router
from app.api.projects import router as projects_router
from app.api.agent import router as agent_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="DevOs API",
    description="AI-powered repository intelligence platform",
    version="0.2.0",
    debug=settings.DEBUG,
)

# ── CORS ──────────────────────────────────────────────────────────────────
_logger = logging.getLogger(__name__)
_cors_origins = settings.cors_origins_list
_logger.info("CORS allowed origins: %s", _cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.auth import router as auth_router

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth_router)          # /api/auth
app.include_router(projects_router)       # /api/projects
app.include_router(repositories_router)  # /api/projects/{id}/repositories/...
app.include_router(search_router)        # /api/search
app.include_router(chat_router)          # /api/chat
app.include_router(agent_router)         # /api/agent

# ── Health ────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok", 
        "env": settings.APP_ENV, 
        "debug": settings.DEBUG,
        "groq_configured": bool(settings.GROQ_API_KEY.strip()),
        "gemini_configured": bool(settings.GEMINI_API_KEY.strip())
    }

@app.get("/", tags=["Root"])
async def root():
    return {"message": "DevOs API — AI-powered repository intelligence 🚀"}
