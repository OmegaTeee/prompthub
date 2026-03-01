"""
Tool registry storage with SQLite backend.

Caches raw MCP tool definitions (before minification) for fast serving
and long-term archival. Mirrors memory/storage.py pattern: lazy singleton,
async initialization, aiosqlite CRUD operations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


class ToolRegistryStorage:
    """
    Tool registry with SQLite persistence.

    Stores current tool snapshots per server and archives old versions.
    Uses per-operation aiosqlite.connect() — no persistent connections.
    """

    def __init__(self, db_path: Path = Path("/tmp/prompthub/tool_registry.db")):
        self.db_path = db_path
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database schema."""
        async with self._init_lock:
            if self._initialized:
                return

            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS tool_cache (
                        server_name   TEXT PRIMARY KEY,
                        tools_json    TEXT NOT NULL,
                        tool_count    INTEGER NOT NULL,
                        raw_size_bytes INTEGER NOT NULL,
                        cached_at     TEXT NOT NULL,
                        expires_at    TEXT,
                        last_served   TEXT,
                        serve_count   INTEGER DEFAULT 0
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS tool_cache_archive (
                        id            INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_name   TEXT NOT NULL,
                        tools_json    TEXT NOT NULL,
                        tool_count    INTEGER NOT NULL,
                        raw_size_bytes INTEGER NOT NULL,
                        cached_at     TEXT NOT NULL,
                        archived_at   TEXT NOT NULL
                    )
                """)

                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_archive_server "
                    "ON tool_cache_archive(server_name)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_archive_date "
                    "ON tool_cache_archive(archived_at)"
                )

                await db.commit()

            self._initialized = True
            logger.info("Initialized tool registry database at %s", self.db_path)

    async def _ensure_init(self) -> None:
        if not self._initialized:
            await self.initialize()

    async def cache_tools(
        self,
        server_name: str,
        tools: list[dict[str, Any]],
        ttl_hours: int = 24,
    ) -> dict[str, Any]:
        """
        Cache a server's tool definitions, archiving any previous snapshot.

        Args:
            server_name: MCP server name
            tools: Raw tool definitions from tools/list response
            ttl_hours: Hours until this cache entry expires

        Returns:
            Snapshot summary dict
        """
        await self._ensure_init()

        now = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        tools_json = json.dumps(tools)
        raw_size = len(tools_json)

        async with aiosqlite.connect(str(self.db_path)) as db:
            # Archive existing snapshot before replacing
            await db.execute("""
                INSERT INTO tool_cache_archive
                    (server_name, tools_json, tool_count, raw_size_bytes, cached_at, archived_at)
                SELECT server_name, tools_json, tool_count, raw_size_bytes, cached_at, ?
                FROM tool_cache
                WHERE server_name = ?
            """, (now, server_name))

            # Upsert current snapshot
            await db.execute("""
                INSERT OR REPLACE INTO tool_cache
                    (server_name, tools_json, tool_count, raw_size_bytes, cached_at, expires_at,
                     last_served, serve_count)
                VALUES (?, ?, ?, ?, ?, ?, NULL, 0)
            """, (server_name, tools_json, len(tools), raw_size, now, expires_at))

            await db.commit()

        logger.info(
            "Cached %d tools for %s (%d bytes, expires %s)",
            len(tools), server_name, raw_size, expires_at,
        )

        return {
            "server_name": server_name,
            "tool_count": len(tools),
            "raw_size_bytes": raw_size,
            "cached_at": now,
            "expires_at": expires_at,
        }

    async def get_cached_tools(
        self, server_name: str
    ) -> list[dict[str, Any]] | None:
        """
        Get cached tools for a server if not expired.

        Updates last_served and serve_count on hit.
        Returns None on miss or expiry.
        """
        await self._ensure_init()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                "SELECT * FROM tool_cache WHERE server_name = ?",
                (server_name,),
            )
            row = await cursor.fetchone()

            if not row:
                return None

            # Check expiry
            expires_at = row["expires_at"]
            if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                logger.debug("Cache expired for %s", server_name)
                return None

            # Update serve stats
            now = datetime.now().isoformat()
            await db.execute("""
                UPDATE tool_cache
                SET last_served = ?, serve_count = serve_count + 1
                WHERE server_name = ?
            """, (now, server_name))
            await db.commit()

            return json.loads(row["tools_json"])

    async def get_snapshot(self, server_name: str) -> dict[str, Any] | None:
        """Get full snapshot metadata (without parsing tools) for a server."""
        await self._ensure_init()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                "SELECT * FROM tool_cache WHERE server_name = ?",
                (server_name,),
            )
            row = await cursor.fetchone()

            if not row:
                return None

            snapshot = dict(row)
            snapshot["tools"] = json.loads(snapshot.pop("tools_json"))
            return snapshot

    async def get_all_cached(self) -> list[dict[str, Any]]:
        """Get summary of all cached snapshots (no tool definitions)."""
        await self._ensure_init()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute("""
                SELECT server_name, tool_count, raw_size_bytes,
                       cached_at, expires_at, last_served, serve_count
                FROM tool_cache
                ORDER BY server_name
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def invalidate(self, server_name: str) -> bool:
        """
        Remove cache entry for a server (e.g., on restart).

        Archives the entry before deleting.
        """
        await self._ensure_init()

        async with aiosqlite.connect(str(self.db_path)) as db:
            now = datetime.now().isoformat()

            # Archive before deleting
            await db.execute("""
                INSERT INTO tool_cache_archive
                    (server_name, tools_json, tool_count, raw_size_bytes, cached_at, archived_at)
                SELECT server_name, tools_json, tool_count, raw_size_bytes, cached_at, ?
                FROM tool_cache
                WHERE server_name = ?
            """, (now, server_name))

            cursor = await db.execute(
                "DELETE FROM tool_cache WHERE server_name = ?",
                (server_name,),
            )
            await db.commit()

            deleted = cursor.rowcount > 0

        if deleted:
            logger.info("Invalidated tool cache for %s", server_name)

        return deleted

    async def invalidate_all(self) -> int:
        """Invalidate all cached tools, archiving them first."""
        await self._ensure_init()

        async with aiosqlite.connect(str(self.db_path)) as db:
            now = datetime.now().isoformat()

            await db.execute("""
                INSERT INTO tool_cache_archive
                    (server_name, tools_json, tool_count, raw_size_bytes, cached_at, archived_at)
                SELECT server_name, tools_json, tool_count, raw_size_bytes, cached_at, ?
                FROM tool_cache
            """, (now,))

            cursor = await db.execute("DELETE FROM tool_cache")
            await db.commit()

            count = cursor.rowcount

        logger.info("Invalidated all tool caches (%d entries)", count)
        return count

    async def archive_expired(self) -> int:
        """Move expired cache entries to archive table."""
        await self._ensure_init()

        now = datetime.now().isoformat()

        async with aiosqlite.connect(str(self.db_path)) as db:
            # Archive expired entries
            await db.execute("""
                INSERT INTO tool_cache_archive
                    (server_name, tools_json, tool_count, raw_size_bytes, cached_at, archived_at)
                SELECT server_name, tools_json, tool_count, raw_size_bytes, cached_at, ?
                FROM tool_cache
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (now, now))

            cursor = await db.execute("""
                DELETE FROM tool_cache
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (now,))
            await db.commit()

            count = cursor.rowcount

        if count > 0:
            logger.info("Archived %d expired tool cache entries", count)

        return count

    async def cleanup_archive(self, retention_days: int = 90) -> int:
        """Delete archived snapshots older than retention period."""
        await self._ensure_init()

        cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "DELETE FROM tool_cache_archive WHERE archived_at < ?",
                (cutoff,),
            )
            await db.commit()
            count = cursor.rowcount

        if count > 0:
            logger.info(
                "Cleaned up %d archived snapshots older than %d days",
                count, retention_days,
            )

        return count

    async def get_stats(self) -> dict[str, Any]:
        """Get aggregate registry statistics."""
        await self._ensure_init()

        async with aiosqlite.connect(str(self.db_path)) as db:
            # Current cache stats
            cursor = await db.execute("""
                SELECT COUNT(*) as servers,
                       COALESCE(SUM(tool_count), 0) as tools,
                       COALESCE(SUM(raw_size_bytes), 0) as size,
                       COALESCE(SUM(serve_count), 0) as serves,
                       MIN(cached_at) as oldest,
                       MAX(cached_at) as newest
                FROM tool_cache
            """)
            row = await cursor.fetchone()

            # Archive count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM tool_cache_archive"
            )
            archive_count = (await cursor.fetchone())[0]

        return {
            "cached_servers": row[0],
            "total_tools": row[1],
            "total_size_bytes": row[2],
            "total_serve_count": row[3],
            "oldest_snapshot": row[4],
            "newest_snapshot": row[5],
            "archived_snapshots": archive_count,
        }

    async def vacuum(self) -> None:
        """Reclaim disk space after bulk deletes."""
        await self._ensure_init()

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("VACUUM")

        logger.info("Vacuumed tool registry database")


# Global singleton
_tool_registry: ToolRegistryStorage | None = None


def get_tool_registry(
    db_path: Path = Path("/tmp/prompthub/tool_registry.db"),
) -> ToolRegistryStorage:
    """Get or create the global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistryStorage(db_path)
    return _tool_registry
