"""
In-memory LRU cache implementation (L1 cache).

This cache provides fast, exact-match caching for prompt enhancement
results. It uses an LRU (Least Recently Used) eviction policy to
bound memory usage.

Features:
- O(1) get/set operations
- LRU eviction when capacity is reached
- Optional TTL per entry
- Thread-safe with asyncio locks
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import Any

from router.cache.base import BaseCache, CacheStats

logger = logging.getLogger(__name__)


def make_cache_key(data: dict | str) -> str:
    """
    Create a deterministic cache key from data.

    Args:
        data: Dictionary or string to hash

    Returns:
        SHA-256 hash of the JSON-serialized data
    """
    if isinstance(data, str):
        content = data
    else:
        # Sort keys for deterministic serialization
        content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class MemoryCache(BaseCache[str, Any]):
    """
    In-memory LRU cache with TTL support.

    This is the L1 cache layer, providing fast exact-match lookups
    for recently enhanced prompts.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600.0,  # 1 hour
    ):
        """
        Initialize the memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float, float | None]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = CacheStats(max_size=max_size)

    async def get(self, key: str) -> Any | None:
        """
        Get a value from the cache.

        Moves the entry to the end (most recently used) on access.
        """
        async with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            value, created_at, ttl = self._cache[key]

            # Check TTL
            if ttl is not None:
                age = time.time() - created_at
                if age > ttl:
                    # Expired
                    del self._cache[key]
                    self._stats.misses += 1
                    self._stats.size = len(self._cache)
                    return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats.hits += 1
            return value

    async def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """
        Set a value in the cache.

        If the cache is at capacity, evicts the least recently used entry.
        """
        if ttl is None:
            ttl = self.default_ttl

        async with self._lock:
            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = (value, time.time(), ttl)
                self._cache.move_to_end(key)
                return

            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                self._stats.evictions += 1
                logger.debug(f"Evicted cache entry: {evicted_key[:8]}...")

            # Add new entry
            self._cache[key] = (value, time.time(), ttl)
            self._stats.size = len(self._cache)

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()
            self._stats.size = 0
            logger.info("Memory cache cleared")

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        return await self.get(key) is not None

    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            size=len(self._cache),
            max_size=self.max_size,
            evictions=self._stats.evictions,
        )

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        removed = 0
        current_time = time.time()

        async with self._lock:
            expired_keys = []
            for key, (_, created_at, ttl) in self._cache.items():
                if ttl is not None and (current_time - created_at) > ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                removed += 1

            self._stats.size = len(self._cache)

        if removed > 0:
            logger.debug(f"Cleaned up {removed} expired cache entries")

        return removed


class EnhancementCache(MemoryCache):
    """
    Specialized cache for prompt enhancement results.

    Provides helper methods for caching enhanced prompts
    with automatic key generation.
    """

    def __init__(
        self,
        max_size: int = 500,
        default_ttl: float = 7200.0,  # 2 hours
    ):
        super().__init__(max_size=max_size, default_ttl=default_ttl)

    async def get_enhanced(
        self,
        prompt: str,
        client_name: str | None = None,
        model: str | None = None,
    ) -> str | None:
        """
        Get a cached enhanced prompt.

        Args:
            prompt: Original prompt
            client_name: Client identifier (affects enhancement rules)
            model: Model used for enhancement

        Returns:
            Cached enhanced prompt or None
        """
        key = make_cache_key({
            "prompt": prompt,
            "client": client_name or "default",
            "model": model or "default",
        })
        return await self.get(key)

    async def set_enhanced(
        self,
        prompt: str,
        enhanced: str,
        client_name: str | None = None,
        model: str | None = None,
        ttl: float | None = None,
    ) -> None:
        """
        Cache an enhanced prompt.

        Args:
            prompt: Original prompt
            enhanced: Enhanced prompt result
            client_name: Client identifier
            model: Model used
            ttl: Custom TTL
        """
        key = make_cache_key({
            "prompt": prompt,
            "client": client_name or "default",
            "model": model or "default",
        })
        await self.set(key, enhanced, ttl)
