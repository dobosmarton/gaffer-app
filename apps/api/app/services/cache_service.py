"""
Cache Service

Provides a unified caching interface with Redis support and in-memory fallback.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as redis

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: timedelta) -> bool:
        """Set a value in cache with TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Check if the cache backend is available."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the cache connection."""
        pass


class InMemoryCacheBackend(CacheBackend):
    """In-memory cache backend for local development or fallback."""

    def __init__(self):
        self._cache: dict[str, tuple[str, datetime]] = {}

    async def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.now(timezone.utc) < expires_at:
                return value
            # Expired - clean up
            del self._cache[key]
        return None

    async def set(self, key: str, value: str, ttl: timedelta) -> bool:
        expires_at = datetime.now(timezone.utc) + ttl
        self._cache[key] = (value, expires_at)
        return True

    async def delete(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        self._cache.clear()


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for distributed caching."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    async def get(self, key: str) -> Optional[str]:
        try:
            value = await self._redis.get(key)
            return value.decode() if value else None
        except Exception as e:
            logger.warning(f"Redis GET error for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl: timedelta) -> bool:
        try:
            await self._redis.setex(key, int(ttl.total_seconds()), value)
            return True
        except Exception as e:
            logger.warning(f"Redis SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis DELETE error for key {key}: {e}")
            return False

    async def ping(self) -> bool:
        try:
            return await self._redis.ping()
        except Exception:
            return False

    async def close(self) -> None:
        await self._redis.aclose()


class CacheService:
    """
    Main cache service with automatic fallback.

    Attempts Redis first, falls back to in-memory if Redis unavailable.
    """

    def __init__(
        self,
        primary: CacheBackend,
        fallback: Optional[CacheBackend] = None,
    ):
        self._primary = primary
        self._fallback = fallback or InMemoryCacheBackend()
        self._using_fallback = False

    @property
    def is_using_fallback(self) -> bool:
        return self._using_fallback

    async def _get_backend(self) -> CacheBackend:
        """Get the active backend, switching to fallback if needed."""
        if self._using_fallback:
            return self._fallback

        if await self._primary.ping():
            return self._primary

        logger.warning("Primary cache unavailable, switching to fallback")
        self._using_fallback = True
        return self._fallback

    async def get(self, key: str) -> Optional[str]:
        backend = await self._get_backend()
        return await backend.get(key)

    async def set(self, key: str, value: str, ttl: timedelta) -> bool:
        backend = await self._get_backend()
        return await backend.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        backend = await self._get_backend()
        return await backend.delete(key)

    async def close(self) -> None:
        await self._primary.close()
        await self._fallback.close()


# Global cache service instance (initialized in lifespan)
_cache_service: Optional[CacheService] = None


async def init_cache_service(settings: Settings) -> CacheService:
    """Initialize the cache service based on settings."""
    global _cache_service

    fallback = InMemoryCacheBackend()

    if settings.redis_enabled:
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False,
            )
            # Test connection
            await redis_client.ping()
            logger.info("Redis cache connected successfully")
            primary = RedisCacheBackend(redis_client)
            _cache_service = CacheService(primary, fallback)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis, using in-memory cache: {e}")
            _cache_service = CacheService(fallback)
    else:
        logger.info("Redis not configured, using in-memory cache")
        _cache_service = CacheService(fallback)

    return _cache_service


async def close_cache_service() -> None:
    """Close the cache service."""
    global _cache_service
    if _cache_service:
        await _cache_service.close()
        _cache_service = None


def get_cache_service() -> CacheService:
    """Dependency for getting the cache service."""
    if _cache_service is None:
        raise RuntimeError("Cache service not initialized")
    return _cache_service
