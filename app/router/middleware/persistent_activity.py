"""
Persistent Activity Log with SQLite Backend.

Provides persistent storage for activity log entries with async SQLite.
Replaces in-memory deque with database persistence.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic import BaseModel

from router.middleware.audit_context import get_audit_context

logger = logging.getLogger(__name__)


class ActivityEntry(BaseModel):
    """A single activity log entry."""

    id: int | None = None
    timestamp: str
    method: str
    path: str
    status: int
    duration: float  # seconds
    client_id: str | None = None
    client_ip: str | None = None
    request_id: str | None = None


class PersistentActivityLog:
    """
    Activity log with SQLite persistence.

    Stores activity entries in SQLite database for persistence across restarts.
    Uses aiosqlite for async database operations without blocking the event loop.
    """

    def __init__(self, db_path: Path = Path("/tmp/agenthub/activity.db")):
        """
        Initialize persistent activity log.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database schema."""
        async with self._init_lock:
            if self._initialized:
                return

            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create schema
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        method TEXT NOT NULL,
                        path TEXT NOT NULL,
                        status INTEGER NOT NULL,
                        duration REAL NOT NULL,
                        client_id TEXT,
                        client_ip TEXT,
                        request_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for common queries
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_timestamp ON activity(timestamp DESC)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_status ON activity(status)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_client_id ON activity(client_id)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_request_id ON activity(request_id)"
                )

                await db.commit()

            self._initialized = True
            logger.info(f"Initialized activity log database at {self.db_path}")

    async def add(
        self,
        method: str,
        path: str,
        status: int,
        duration: float,
    ) -> None:
        """
        Add a new activity entry.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status: HTTP status code
            duration: Request duration in seconds
        """
        if not self._initialized:
            await self.initialize()

        # Get audit context (may be None if not in request context)
        context = get_audit_context()

        timestamp = datetime.now().strftime("%H:%M:%S")

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT INTO activity (timestamp, method, path, status, duration, client_id, client_ip, request_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    method,
                    path,
                    status,
                    duration,
                    context.get("client_id"),
                    context.get("client_ip"),
                    context.get("request_id"),
                ),
            )
            await db.commit()

    async def get_recent(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """
        Get most recent activity entries.

        Args:
            limit: Maximum entries to return
            offset: Number of entries to skip (for pagination)

        Returns:
            List of activity entries (newest first)
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT id, timestamp, method, path, status, duration, client_id, client_ip, request_id
                FROM activity
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def query(
        self,
        method: str | None = None,
        status_min: int | None = None,
        status_max: int | None = None,
        client_id: str | None = None,
        request_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Query activity log with filters.

        Args:
            method: Filter by HTTP method
            status_min: Minimum status code
            status_max: Maximum status code
            client_id: Filter by client ID
            request_id: Filter by request ID
            limit: Maximum entries to return
            offset: Number of entries to skip

        Returns:
            Filtered activity entries
        """
        if not self._initialized:
            await self.initialize()

        # Build dynamic query
        where_clauses = []
        params = []

        if method:
            where_clauses.append("method = ?")
            params.append(method)

        if status_min is not None:
            where_clauses.append("status >= ?")
            params.append(status_min)

        if status_max is not None:
            where_clauses.append("status <= ?")
            params.append(status_max)

        if client_id:
            where_clauses.append("client_id = ?")
            params.append(client_id)

        if request_id:
            where_clauses.append("request_id = ?")
            params.append(request_id)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT id, timestamp, method, path, status, duration, client_id, client_ip, request_id
            FROM activity
            {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def count(
        self,
        method: str | None = None,
        status_min: int | None = None,
        status_max: int | None = None,
        client_id: str | None = None,
    ) -> int:
        """
        Count activity entries matching filters.

        Args:
            method: Filter by HTTP method
            status_min: Minimum status code
            status_max: Maximum status code
            client_id: Filter by client ID

        Returns:
            Total count of matching entries
        """
        if not self._initialized:
            await self.initialize()

        # Build dynamic query
        where_clauses = []
        params = []

        if method:
            where_clauses.append("method = ?")
            params.append(method)

        if status_min is not None:
            where_clauses.append("status >= ?")
            params.append(status_min)

        if status_max is not None:
            where_clauses.append("status <= ?")
            params.append(status_max)

        if client_id:
            where_clauses.append("client_id = ?")
            params.append(client_id)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"SELECT COUNT(*) FROM activity {where_sql}"

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def clear(self) -> None:
        """Clear all activity entries."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("DELETE FROM activity")
            await db.commit()

        logger.info("Cleared all activity log entries")

    async def cleanup_old_entries(self, days: int = 30) -> int:
        """
        Delete entries older than specified days.

        Args:
            days: Delete entries older than this many days

        Returns:
            Number of entries deleted
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                """
                DELETE FROM activity
                WHERE created_at < datetime('now', '-' || ? || ' days')
                """,
                (days,),
            )
            await db.commit()
            deleted = cursor.rowcount

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} activity entries older than {days} days")

        return deleted

    @property
    async def size(self) -> int:
        """Current number of entries."""
        return await self.count()


# Global persistent activity log instance
persistent_activity_log: PersistentActivityLog | None = None


def get_persistent_activity_log(
    db_path: Path = Path("/tmp/agenthub/activity.db"),
) -> PersistentActivityLog:
    """Get or create the global persistent activity log instance."""
    global persistent_activity_log
    if persistent_activity_log is None:
        persistent_activity_log = PersistentActivityLog(db_path)
    return persistent_activity_log
