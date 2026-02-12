"""
Abstract base class for cache implementations.

This provides a common interface for different cache backends,
allowing easy swapping between L1 (memory) and L2 (semantic) caches.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type


class CacheStats(BaseModel):
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheEntry(BaseModel, Generic[V]):
    """A single cache entry with metadata."""

    value: Any  # The cached value
    created_at: float  # Timestamp when entry was created
    accessed_at: float  # Timestamp of last access
    access_count: int = 0  # Number of times accessed
    ttl: float | None = None  # Time-to-live in seconds


class BaseCache(ABC, Generic[K, V]):
    """
    Abstract base class for cache implementations.

    All cache implementations should inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    async def get(self, key: K) -> V | None:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    async def set(self, key: K, value: V, ttl: float | None = None) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for default)
        """
        pass

    @abstractmethod
    async def delete(self, key: K) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from the cache."""
        pass

    @abstractmethod
    async def exists(self, key: K) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired
        """
        pass

    @abstractmethod
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        pass

    async def get_or_set(
        self, key: K, factory: Any, ttl: float | None = None
    ) -> V:
        """
        Get a value from cache, or compute and cache it if not found.

        Args:
            key: Cache key
            factory: Async callable that produces the value
            ttl: Time-to-live in seconds

        Returns:
            Cached or computed value
        """
        value = await self.get(key)
        if value is not None:
            return value

        # Compute value
        value = await factory()
        await self.set(key, value, ttl)
        return value
