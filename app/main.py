import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, session, mindmap, auth
from app.config import settings
from app.database import db
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting Clearity Backend...")
    logger.info(f"Environment: {settings.FAST_MODEL} (fast), {settings.DEEP_MODEL} (deep)")

    await db.connect()

    yield

    logger.info("Shutting down Clearity Backend...")
    await db.disconnect()


app = FastAPI(
    title="Clearity API",
    description="AI clarity engine for people who feel mentally overloaded, scattered, or stuck",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(session.router, prefix="/api", tags=["Sessions"])
app.include_router(mindmap.router, prefix="/api", tags=["Mind Map"])


@app.get("/")
async def root():
    return {
        "service": "Clearity API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    try:
        await db.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    import sys
    import os

    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=55110,
        reload=True,
        log_level="info"
    )
