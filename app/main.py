import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, session, mindmap, auth
from app.config import settings
from app.database import db
from app.logging_config import setup_logging
from app.rate_limit import limiter  # Import limiter from separate module
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)
SENSITIVE_PATHS = {"/api/auth/login", "/api/auth/register"}


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

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler - catches all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_details = {
        "path": request.url.path,
        "method": request.method,
        "client": request.client.host if request.client else "unknown",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }

    if request.url.path not in SENSITIVE_PATHS:
        logger.error(
            f"Unexpected error in {request.method} {request.url.path}: {exc}",
            extra=error_details,
            exc_info=True
        )

    # Return user-friendly error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
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
