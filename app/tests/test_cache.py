"""
Tests for cache module (L1 in-memory LRU cache).

Verifies:
- L1 cache hits and misses
- LRU eviction policy
- Stats tracking
- Size limits
"""

import pytest
from router.cache.memory import MemoryCache


class TestMemoryCache:
    """Test cases for in-memory LRU cache."""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache returns stored value on hit."""
        cache = MemoryCache(max_size=10)

        await cache.set("key1", "value1")
        result = await cache.get("key1")

        assert result == "value1"
        stats = cache.stats()
        assert stats.hits == 1
        assert stats.misses == 0

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache returns None on miss."""
        cache = MemoryCache(max_size=10)

        result = await cache.get("nonexistent")

        assert result is None
        stats = cache.stats()
        assert stats.hits == 0
        assert stats.misses == 1

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when cache exceeds max_size."""
        cache = MemoryCache(max_size=3)

        # Fill cache to capacity
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Add one more item, should evict oldest (key1)
        await cache.set("key4", "value4")

        assert await cache.get("key1") is None  # Evicted
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

        stats = cache.stats()
        assert stats.size == 3

    @pytest.mark.asyncio
    async def test_lru_access_updates_order(self):
        """Test accessing an item moves it to end of LRU queue."""
        cache = MemoryCache(max_size=3)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to move it to end
        await cache.get("key1")

        # Add key4, should evict key2 (now oldest)
        await cache.set("key4", "value4")

        assert await cache.get("key1") == "value1"  # Still present
        assert await cache.get("key2") is None  # Evicted
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test cache statistics are tracked correctly."""
        cache = MemoryCache(max_size=5)

        # Perform various operations
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        await cache.get("key1")  # Hit
        await cache.get("key3")  # Miss

        stats = cache.stats()
        assert stats.hits == 2
        assert stats.misses == 2
        assert stats.size == 1
        assert stats.max_size == 5

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing cache removes all entries."""
        cache = MemoryCache(max_size=10)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        stats = cache.stats()
        assert stats.size == 0

    @pytest.mark.asyncio
    async def test_update_existing_key(self):
        """Test updating existing key doesn't increase size."""
        cache = MemoryCache(max_size=3)

        await cache.set("key1", "value1")
        await cache.set("key1", "value2")

        assert await cache.get("key1") == "value2"
        stats = cache.stats()
        assert stats.size == 1

    @pytest.mark.asyncio
    async def test_empty_cache_stats(self):
        """Test stats for empty cache."""
        cache = MemoryCache(max_size=10)

        stats = cache.stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.size == 0
        assert stats.max_size == 10
