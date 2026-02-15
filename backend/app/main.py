"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.routers import (
    providers,
    feeds,
    articles,
    content_router,
    scripts,
    audio,
    video,
    news_router,
    health,
    youtube_router,
    book_router,
)
from app.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Setup logging
    setup_logging()
    logger.info("application_startup", version="0.1.0")
    
    # Initialize database
    init_db()
    logger.info("database_initialized")
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("application_shutdown")


app = FastAPI(
    title="AIVideoGen API",
    description="Automated AI news video generation platform",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:5174",  # Alternate port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(providers.router)
app.include_router(feeds.router)
app.include_router(articles.router)
app.include_router(content_router.router)
app.include_router(scripts.router)
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(video.router, prefix="/api/video", tags=["video"])
app.include_router(news_router.router)
app.include_router(health.router)
app.include_router(youtube_router.router)
app.include_router(book_router.router)




@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": "AIVideoGen API is running",
        "version": "0.1.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check with provider status."""
    return {
        "status": "healthy",
        "database": "connected",
        "llm_provider": settings.default_llm_provider,
        "tts_provider": settings.default_tts_provider,
        "providers_available": {
            "gemini": bool(settings.google_api_key),
            "openai": bool(settings.openai_api_key),
            "claude": bool(settings.anthropic_api_key),
            "google_tts": bool(settings.google_cloud_project_id),
            "elevenlabs": bool(settings.elevenlabs_api_key)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

