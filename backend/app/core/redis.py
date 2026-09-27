import redis.asyncio as aioredis
from app.core.config import settings

# Global async Redis client instance
redis_client = aioredis.from_url(
    settings.REDIS_URI,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> aioredis.Redis:
    """Dependency / accessor for async Redis client."""
    return redis_client


async def check_redis_connection() -> dict:
    """Verify Redis connection."""
    try:
        pong = await redis_client.ping()
        if pong:
            return {"status": "connected", "details": "Redis operational"}
        return {"status": "error", "details": "Ping failed"}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}
