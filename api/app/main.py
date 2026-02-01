from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import subscribers, newsletters, tracking, analytics

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Newsletter subscription and engagement tracking API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(subscribers.router)
app.include_router(newsletters.router)
app.include_router(tracking.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
