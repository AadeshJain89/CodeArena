from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.topics import router as topics_router
from app.api.problems import router as problems_router
from app.api.execution import router as execution_router
from app.api.submissions import router as submissions_router
from app.api.diagnostic import router as diagnostic_router
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
    version="0.6.0",
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

app.include_router(
    topics_router,
    prefix=f"{settings.API_V1_STR}/topics",
    tags=["Topics"],
)

app.include_router(
    problems_router,
    prefix=f"{settings.API_V1_STR}/problems",
    tags=["Problems"],
)

app.include_router(
    execution_router,
    prefix=f"{settings.API_V1_STR}/execute",
    tags=["Execution"],
)

app.include_router(
    submissions_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["Submissions"],
)

app.include_router(
    diagnostic_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["Diagnostic"],
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to CodeArena API",
        "docs": "/docs",
        "health": "/health",
        "topics": f"{settings.API_V1_STR}/topics",
        "problems": f"{settings.API_V1_STR}/problems",
        "execute": f"{settings.API_V1_STR}/execute",
        "submissions": f"{settings.API_V1_STR}/submissions",
        "diagnostic": f"{settings.API_V1_STR}/diagnostic",
    }
