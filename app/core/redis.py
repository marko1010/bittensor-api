import redis.asyncio as redis
from app.core.config import settings

_redis_pool = None

def get_redis_pool():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            max_connections=100
        )
    return _redis_pool

def get_redis_client():
    return redis.Redis(connection_pool=get_redis_pool())