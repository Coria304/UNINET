"""Cliente Redis compartido (cache, retos MFA, rate limiting)."""

from functools import lru_cache

import redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> redis.Redis:
    """Singleton de cliente Redis con decodificación UTF-8."""
    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True)
