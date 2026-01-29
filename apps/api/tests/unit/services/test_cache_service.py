"""
Unit tests for CacheService.
"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.cache_service import (
    CacheService,
    InMemoryCacheBackend,
    RedisCacheBackend,
)


class TestInMemoryCacheBackend:
    """Tests for the in-memory cache backend."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Can set and retrieve a value."""
        backend = InMemoryCacheBackend()

        await backend.set("key", "value", timedelta(minutes=5))
        result = await backend.get("key")

        assert result == "value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key_returns_none(self):
        """Getting nonexistent key returns None."""
        backend = InMemoryCacheBackend()

        result = await backend.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_expired_value_returns_none(self):
        """Expired values return None and are cleaned up."""
        backend = InMemoryCacheBackend()

        # Set with negative TTL (already expired)
        await backend.set("key", "value", timedelta(seconds=-1))

        result = await backend.get("key")

        assert result is None
        assert "key" not in backend._cache

    @pytest.mark.asyncio
    async def test_delete_removes_key(self):
        """Delete removes the key from cache."""
        backend = InMemoryCacheBackend()

        await backend.set("key", "value", timedelta(minutes=5))
        deleted = await backend.delete("key")
        result = await backend.get("key")

        assert deleted is True
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self):
        """Deleting nonexistent key returns False."""
        backend = InMemoryCacheBackend()

        deleted = await backend.delete("nonexistent")

        assert deleted is False

    @pytest.mark.asyncio
    async def test_ping_always_returns_true(self):
        """In-memory backend ping always returns True."""
        backend = InMemoryCacheBackend()

        assert await backend.ping() is True

    @pytest.mark.asyncio
    async def test_close_clears_cache(self):
        """Closing backend clears the cache."""
        backend = InMemoryCacheBackend()

        await backend.set("key", "value", timedelta(minutes=5))
        await backend.close()

        assert len(backend._cache) == 0


class TestCacheServiceFallback:
    """Tests for cache service fallback behavior."""

    @pytest.mark.asyncio
    async def test_uses_primary_when_available(self):
        """Uses primary backend when it responds to ping."""
        primary = MagicMock(spec=InMemoryCacheBackend)
        primary.ping = AsyncMock(return_value=True)
        primary.get = AsyncMock(return_value="primary-value")

        fallback = MagicMock(spec=InMemoryCacheBackend)

        service = CacheService(primary, fallback)

        result = await service.get("key")

        assert result == "primary-value"
        primary.get.assert_called_once_with("key")
        fallback.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_when_primary_unavailable(self):
        """Falls back when primary ping fails."""
        primary = MagicMock(spec=InMemoryCacheBackend)
        primary.ping = AsyncMock(return_value=False)

        fallback = MagicMock(spec=InMemoryCacheBackend)
        fallback.get = AsyncMock(return_value="fallback-value")

        service = CacheService(primary, fallback)

        result = await service.get("key")

        assert result == "fallback-value"
        assert service.is_using_fallback is True

    @pytest.mark.asyncio
    async def test_stays_on_fallback_once_switched(self):
        """Once switched to fallback, stays there."""
        primary = MagicMock(spec=InMemoryCacheBackend)
        primary.ping = AsyncMock(return_value=False)

        fallback = MagicMock(spec=InMemoryCacheBackend)
        fallback.get = AsyncMock(return_value="fallback-value")

        service = CacheService(primary, fallback)

        # First call switches to fallback
        await service.get("key1")

        # Primary is "back" but we should still use fallback
        primary.ping = AsyncMock(return_value=True)
        await service.get("key2")

        # Should still be using fallback (2 calls total)
        assert fallback.get.call_count == 2

    @pytest.mark.asyncio
    async def test_set_uses_active_backend(self):
        """Set operation uses the active backend."""
        primary = MagicMock(spec=InMemoryCacheBackend)
        primary.ping = AsyncMock(return_value=True)
        primary.set = AsyncMock(return_value=True)

        fallback = MagicMock(spec=InMemoryCacheBackend)

        service = CacheService(primary, fallback)

        result = await service.set("key", "value", timedelta(minutes=5))

        assert result is True
        primary.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_uses_active_backend(self):
        """Delete operation uses the active backend."""
        primary = MagicMock(spec=InMemoryCacheBackend)
        primary.ping = AsyncMock(return_value=True)
        primary.delete = AsyncMock(return_value=True)

        fallback = MagicMock(spec=InMemoryCacheBackend)

        service = CacheService(primary, fallback)

        result = await service.delete("key")

        assert result is True
        primary.delete.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_close_closes_both_backends(self):
        """Close operation closes both primary and fallback."""
        primary = MagicMock(spec=InMemoryCacheBackend)
        primary.close = AsyncMock()

        fallback = MagicMock(spec=InMemoryCacheBackend)
        fallback.close = AsyncMock()

        service = CacheService(primary, fallback)

        await service.close()

        primary.close.assert_called_once()
        fallback.close.assert_called_once()
