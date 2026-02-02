import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import subscribers, newsletters, tracking, analytics, auth, contact
from app.logging_config import setup_logging, get_logger
from app.email import init_resend
from app.database import db

# Setup logging
log_json = os.getenv("LOG_FORMAT", "json") == "json"
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(json_output=log_json, level=log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Newsletter API", version=settings.api_version)
    init_resend()

    yield

    # Shutdown
    logger.info("Shutting down Newsletter API")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Newsletter subscription and engagement tracking API",
    lifespan=lifespan
)

# CORS - configure via CORS_ORIGINS env var (comma-separated)
cors_origins = settings.cors_origins_list
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Routers
app.include_router(auth.router)
app.include_router(subscribers.router)
app.include_router(newsletters.router)
app.include_router(tracking.router)
app.include_router(analytics.router)
app.include_router(contact.router)


@app.get("/")
async def root():
    """API information endpoint."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Basic health check."""
    return {"status": "healthy"}


@app.get("/health/ready")
async def readiness():
    """
    Readiness check - verifies all dependencies are available.
    Use this for Kubernetes readiness probes.
    """
    checks = {
        "api": "healthy",
        "database": "unknown"
    }

    # Check database connectivity
    try:
        await db.execute("RETURN 1 as ping")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "checks": checks
        }

    return {
        "status": "healthy",
        "checks": checks
    }


@app.get("/health/live")
async def liveness():
    """
    Liveness check - verifies the application is running.
    Use this for Kubernetes liveness probes.
    """
    return {"status": "alive"}
