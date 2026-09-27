from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.core.config import settings
from app.core.db import engine
from app.core.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan manager."""
    # Startup actions
    yield
    # Shutdown actions
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CodeArena Backend API",
    version="0.2.0",
    lifespan=lifespan,
)

# Configured CORS middleware using environment-based origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registrations
app.include_router(health_router, tags=["Health"])
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])

app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"],
)

app.include_router(
    admin_router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["Admin"],
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to CodeArena API",
        "docs": "/docs",
        "health": "/health",
        "auth": f"{settings.API_V1_STR}/auth",
    }
