"""
Write-through L1+L2 persistent cache.

Composes an in-memory MemoryCache (L1) with a SQLite backend (L2)
so cache entries survive router restarts. The hot path (L1 hit)
adds zero overhead; L2 is only queried on L1 misses.

Connection pattern: per-operation aiosqlite.connect() — matches
persistent_activity.py and memory/storage.py conventions.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import aiosqlite

from router.cache.base import BaseCache, CacheStats
from router.cache.memory import MemoryCache

logger = logging.getLogger(__name__)


class PersistentCache(BaseCache[str, Any]):
    """
    Write-through L1 (memory) + L2 (SQLite) cache.

    On set(): writes to both L1 and L2.
    On get(): checks L1 first; on miss, checks L2 and promotes to L1.
    On startup: optionally warms L1 from L2.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600.0,
        db_path: Path | None = None,
        warm_on_init: bool = True,
    ):
        self._l1 = MemoryCache(max_size=max_size, default_ttl=default_ttl)
        self.max_size = max_size
        self.default_ttl = default_ttl
        if db_path is None:
            from router.config import get_settings
            db_path = Path(get_settings().cache_db_path)
        self.db_path = db_path
        self._warm_on_init = warm_on_init
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self._l2_hits = 0

    async def initialize(self) -> None:
        """Create SQLite schema and optionally warm L1."""
        async with self._init_lock:
            if self._initialized:
                return

            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        ttl REAL,
                        accessed_at REAL NOT NULL
                    )
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_accessed
                    ON cache_entries(accessed_at DESC)
                """)
                await db.commit()

            self._initialized = True
            logger.info(f"Persistent cache initialized at {self.db_path}")

            if self._warm_on_init:
                loaded = await self._warm_l1()
                if loaded > 0:
                    logger.info(
                        f"Warmed L1 cache with {loaded} entries from L2"
                    )

    async def _warm_l1(self) -> int:
        """Load most recently accessed entries from L2 into L1."""
        now = time.time()
        loaded = 0

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT key, value, created_at, ttl, accessed_at
                FROM cache_entries
                ORDER BY accessed_at DESC
                LIMIT ?
                """,
                (self.max_size,),
            )
            rows = await cursor.fetchall()

        for row in rows:
            created_at = row["created_at"]
            ttl = row["ttl"]

            # Skip expired entries
            if ttl is not None and (now - created_at) > ttl:
                continue

            try:
                value = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                value = row["value"]

            await self._l1.set(row["key"], value, ttl)
            loaded += 1

        return loaded

    async def get(self, key: str) -> Any | None:
        """Check L1, fall back to L2, promote on L2 hit."""
        # L1 lookup
        value = await self._l1.get(key)
        if value is not None:
            return value

        # L1 miss — check L2
        if not self._initialized:
            return None

        now = time.time()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT value, created_at, ttl FROM cache_entries "
                "WHERE key = ?",
                (key,),
            )
            row = await cursor.fetchone()

        if row is None:
            return None

        # TTL check
        created_at = row["created_at"]
        ttl = row["ttl"]
        if ttl is not None and (now - created_at) > ttl:
            # Expired in L2 — clean up opportunistically
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute(
                    "DELETE FROM cache_entries WHERE key = ?", (key,)
                )
                await db.commit()
            return None

        # L2 hit — deserialize and promote to L1
        try:
            value = json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            value = row["value"]

        self._l2_hits += 1

        # Promote to L1 (don't count as a new L1 miss)
        await self._l1.set(key, value, ttl)
        # Undo the miss that _l1.get() recorded above
        self._l1._stats.misses -= 1

        # Update accessed_at in L2
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE cache_entries SET accessed_at = ? WHERE key = ?",
                (now, key),
            )
            await db.commit()

        return value

    async def set(
        self, key: str, value: Any, ttl: float | None = None
    ) -> None:
        """Write to both L1 and L2."""
        if ttl is None:
            ttl = self.default_ttl

        # L1
        await self._l1.set(key, value, ttl)

        # L2
        if not self._initialized:
            return

        now = time.time()
        serialized = json.dumps(value)

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO cache_entries
                (key, value, created_at, ttl, accessed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, serialized, now, ttl, now),
            )
            await db.commit()

    async def delete(self, key: str) -> bool:
        """Delete from both L1 and L2."""
        deleted = await self._l1.delete(key)

        if self._initialized:
            async with aiosqlite.connect(str(self.db_path)) as db:
                cursor = await db.execute(
                    "DELETE FROM cache_entries WHERE key = ?", (key,)
                )
                await db.commit()
                if cursor.rowcount > 0:
                    deleted = True

        return deleted

    async def clear(self) -> None:
        """Clear both L1 and L2."""
        await self._l1.clear()

        if self._initialized:
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("DELETE FROM cache_entries")
                await db.commit()

        logger.info("Persistent cache cleared (L1 + L2)")

    async def exists(self, key: str) -> bool:
        """Check if key exists in L1 or L2."""
        return await self.get(key) is not None

    def stats(self) -> CacheStats:
        """Get combined L1 + L2 stats."""
        l1_stats = self._l1.stats()
        return CacheStats(
            hits=l1_stats.hits,
            misses=l1_stats.misses,
            size=l1_stats.size,
            max_size=l1_stats.max_size,
            evictions=l1_stats.evictions,
            l2_hits=self._l2_hits,
            l2_size=self._get_l2_size_sync(),
        )

    def _get_l2_size_sync(self) -> int:
        """Return last known L2 size (updated async)."""
        return self._l2_size_cache

    @property
    def _l2_size_cache(self) -> int:
        """Cached L2 size, updated by async operations."""
        if not hasattr(self, "_l2_size_value"):
            self._l2_size_value = 0
        return self._l2_size_value

    async def refresh_l2_size(self) -> int:
        """Query actual L2 size from SQLite."""
        if not self._initialized:
            return 0

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM cache_entries"
            )
            row = await cursor.fetchone()
            count = row[0] if row else 0

        self._l2_size_value = count
        return count

    async def cleanup_expired(self) -> int:
        """Remove expired entries from both L1 and L2."""
        removed_l1 = await self._l1.cleanup_expired()

        removed_l2 = 0
        if self._initialized:
            now = time.time()
            async with aiosqlite.connect(str(self.db_path)) as db:
                cursor = await db.execute(
                    """
                    DELETE FROM cache_entries
                    WHERE ttl IS NOT NULL
                    AND (? - created_at) > ttl
                    """,
                    (now,),
                )
                await db.commit()
                removed_l2 = cursor.rowcount

        total = removed_l1 + removed_l2
        if total > 0:
            logger.debug(
                f"Cleaned up {removed_l1} L1 + {removed_l2} L2 "
                f"expired cache entries"
            )
        return total

    async def close(self) -> None:
        """Lifecycle hook for clean shutdown."""
        if self._initialized:
            await self.refresh_l2_size()
            logger.info(
                f"Persistent cache closing "
                f"(L2 size: {self._l2_size_value})"
            )
