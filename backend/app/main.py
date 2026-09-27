from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.core.config import settings
from app.core.db import engine
from app.core.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan manager."""
    # Startup actions
    yield
    # Shutdown actions: close db engine and redis connection
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CodeArena Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Health Check Router
app.include_router(health_router, tags=["Health"])
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to CodeArena API",
        "docs": "/docs",
        "health": "/health",
    }
