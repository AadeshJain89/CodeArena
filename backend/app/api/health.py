from fastapi import APIRouter, status
from app.core.config import settings
from app.core.db import check_db_connection
from app.core.redis import check_redis_connection

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint verifying FastAPI app, PostgreSQL, and Redis status."""
    db_health = await check_db_connection()
    redis_health = await check_redis_connection()

    all_ok = (
        db_health.get("status") == "connected"
        and redis_health.get("status") == "connected"
    )

    return {
        "status": "ok" if all_ok else "degraded",
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": db_health,
            "redis": redis_health,
        },
    }
