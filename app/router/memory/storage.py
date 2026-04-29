"""
Session storage with SQLite backend.

Mirrors persistent_activity.py pattern: lazy singleton, async initialization,
aiosqlite CRUD operations, automatic client_id enrichment from audit context.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiosqlite

from router.middleware.audit_context import get_audit_context

logger = logging.getLogger(__name__)


class SessionStorage:
    """
    Session storage with SQLite persistence.

    Stores sessions, facts, and memory blocks. Mirrors PersistentActivityLog pattern
    with lazy singleton initialization guarded by asyncio.Lock().
    """

    def __init__(self, db_path: Path | None = None):
        """Initialize session storage."""
        if db_path is None:
            from router.config import get_settings
            db_path = Path(get_settings().memory_db_path)
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
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        client_id TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        context_summary TEXT,
                        memory_mcp_sync BOOLEAN DEFAULT 0
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS session_facts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                        fact TEXT NOT NULL,
                        tags TEXT DEFAULT '[]',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        relevance_score REAL DEFAULT 1.0,
                        source TEXT DEFAULT 'manual'
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS session_memory_blocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        expires_at DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(session_id, key)
                    )
                """)

                # Create indexes
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sessions_client ON sessions(client_id)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_facts_session ON session_facts(session_id)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_facts_tags ON session_facts(tags)"
                )
                await db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_blocks_session ON session_memory_blocks(session_id)"
                )

                await db.commit()

            self._initialized = True
            logger.info(f"Initialized session storage database at {self.db_path}")

    async def create_session(
        self,
        session_id: str | None = None,
        client_id: str | None = None,
        memory_mcp_sync: bool = False,
    ) -> dict[str, Any]:
        """
        Create a new session.

        Args:
            session_id: Session ID (auto-UUID if omitted)
            client_id: Client ID (from audit context if omitted)
            memory_mcp_sync: Enable Memory MCP sync

        Returns:
            SessionResponse dict
        """
        if not self._initialized:
            await self.initialize()

        # Auto-generate session_id if omitted
        if not session_id:
            session_id = str(uuid4())

        # Get client_id from audit context if omitted
        if not client_id:
            context = get_audit_context()
            client_id = context.get("client_id") or "unknown"

        now = datetime.now().isoformat()

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT INTO sessions (id, client_id, created_at, last_accessed, status, memory_mcp_sync)
                VALUES (?, ?, ?, ?, 'active', ?)
                """,
                (session_id, client_id, now, now, memory_mcp_sync),
            )
            await db.commit()

        return {
            "id": session_id,
            "client_id": client_id,
            "created_at": now,
            "last_accessed": now,
            "status": "active",
            "context_summary": None,
            "memory_mcp_sync": memory_mcp_sync,
            "fact_count": 0,
        }

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session details with fact count."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            # Get session
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            session = dict(row)

            # Count facts
            cursor = await db.execute(
                "SELECT COUNT(*) FROM session_facts WHERE session_id = ?",
                (session_id,),
            )
            count_row = await cursor.fetchone()
            session["fact_count"] = count_row[0] if count_row else 0

            return session

    async def list_sessions(
        self,
        client_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List sessions with optional filters.

        Args:
            client_id: Filter by client_id
            status: Filter by status (active|closed)
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (sessions, total_count)
        """
        if not self._initialized:
            await self.initialize()

        # Build query
        where_clauses = []
        params = []

        if client_id:
            where_clauses.append("client_id = ?")
            params.append(client_id)

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            # Get total count
            count_query = f"SELECT COUNT(*) FROM sessions {where_sql}"
            cursor = await db.execute(count_query, params)
            count_row = await cursor.fetchone()
            total = count_row[0] if count_row else 0

            # Get paginated results
            query = f"""
                SELECT * FROM sessions
                {where_sql}
                ORDER BY last_accessed DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            sessions = []
            for row in rows:
                session = dict(row)

                # Count facts for each session
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM session_facts WHERE session_id = ?",
                    (session["id"],),
                )
                count_row = await cursor.fetchone()
                session["fact_count"] = count_row[0] if count_row else 0

                sessions.append(session)

            return sessions, total

    async def touch_session(self, session_id: str) -> None:
        """Update last_accessed timestamp."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE sessions SET last_accessed = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id),
            )
            await db.commit()

    async def close_session(self, session_id: str) -> None:
        """Close a session (mark status as closed)."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE sessions SET status = ? WHERE id = ?", ("closed", session_id)
            )
            await db.commit()

    async def add_fact(
        self,
        session_id: str,
        fact: str,
        tags: list[str] | None = None,
        source: str = "manual",
    ) -> dict[str, Any]:
        """Add a fact to a session."""
        if not self._initialized:
            await self.initialize()

        tags = tags or []

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                """
                INSERT INTO session_facts (session_id, fact, tags, source, relevance_score)
                VALUES (?, ?, ?, ?, 1.0)
                """,
                (session_id, fact, json.dumps(tags), source),
            )
            await db.commit()
            fact_id = cursor.lastrowid

            # Touch session
            await db.execute(
                "UPDATE sessions SET last_accessed = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id),
            )
            await db.commit()

        return {
            "id": fact_id,
            "session_id": session_id,
            "fact": fact,
            "tags": tags,
            "created_at": datetime.now().isoformat(),
            "relevance_score": 1.0,
            "source": source,
        }

    async def get_facts(
        self,
        session_id: str,
        tags: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get facts for a session with optional tag filter."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            if tags:
                # Filter by tags (JSON array contains)
                query = f"""
                    SELECT * FROM session_facts
                    WHERE session_id = ? AND (
                        {" OR ".join(["json_extract(tags, '$[*]') LIKE ?" for _ in tags])}
                    )
                    ORDER BY relevance_score DESC, created_at DESC
                    LIMIT ?
                """
                params = [session_id] + tags + [limit]
            else:
                query = """
                    SELECT * FROM session_facts
                    WHERE session_id = ?
                    ORDER BY relevance_score DESC, created_at DESC
                    LIMIT ?
                """
                params = [session_id, limit]

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            facts = []
            for row in rows:
                fact = dict(row)
                fact["tags"] = json.loads(fact.get("tags", "[]"))
                facts.append(fact)

            return facts

    async def delete_fact(self, session_id: str, fact_id: int) -> bool:
        """Delete a fact."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "DELETE FROM session_facts WHERE id = ? AND session_id = ?",
                (fact_id, session_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def upsert_memory_block(
        self,
        session_id: str,
        key: str,
        value: Any,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        """Upsert a memory block (insert or update)."""
        if not self._initialized:
            await self.initialize()

        now = datetime.now().isoformat()
        value_str = json.dumps(value)

        async with aiosqlite.connect(str(self.db_path)) as db:
            # Check if exists
            cursor = await db.execute(
                "SELECT id FROM session_memory_blocks WHERE session_id = ? AND key = ?",
                (session_id, key),
            )
            existing = await cursor.fetchone()

            if existing:
                # Update
                block_id = existing[0]
                await db.execute(
                    """
                    UPDATE session_memory_blocks
                    SET value = ?, expires_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (value_str, expires_at, now, block_id),
                )
            else:
                # Insert
                cursor = await db.execute(
                    """
                    INSERT INTO session_memory_blocks
                    (session_id, key, value, expires_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (session_id, key, value_str, expires_at, now, now),
                )
                block_id = cursor.lastrowid

            await db.commit()

            # Touch session
            await db.execute(
                "UPDATE sessions SET last_accessed = ? WHERE id = ?",
                (now, session_id),
            )
            await db.commit()

        return {
            "id": block_id,
            "session_id": session_id,
            "key": key,
            "value": value,
            "expires_at": expires_at,
            "created_at": now,
            "updated_at": now,
        }

    async def get_memory_block(
        self, session_id: str, key: str
    ) -> dict[str, Any] | None:
        """Get a memory block by key."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                "SELECT * FROM session_memory_blocks WHERE session_id = ? AND key = ?",
                (session_id, key),
            )
            row = await cursor.fetchone()

            if not row:
                return None

            block = dict(row)
            block["value"] = json.loads(block["value"])
            return block

    async def get_all_memory_blocks(
        self, session_id: str
    ) -> list[dict[str, Any]]:
        """Get all memory blocks for a session."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                "SELECT * FROM session_memory_blocks WHERE session_id = ?",
                (session_id,),
            )
            rows = await cursor.fetchall()

            blocks = []
            for row in rows:
                block = dict(row)
                block["value"] = json.loads(block["value"])
                blocks.append(block)

            return blocks

    async def delete_memory_block(self, session_id: str, key: str) -> bool:
        """Delete a memory block."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "DELETE FROM session_memory_blocks WHERE session_id = ? AND key = ?",
                (session_id, key),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def decay_relevance_scores(self, decay_factor: float = 0.95) -> int:
        """
        Decay all fact relevance scores.

        Args:
            decay_factor: Multiply all scores by this factor (0.95 = 5% decay)

        Returns:
            Number of rows updated
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "UPDATE session_facts SET relevance_score = relevance_score * ?",
                (decay_factor,),
            )
            await db.commit()
            return cursor.rowcount

    async def cleanup_expired_blocks(self) -> int:
        """
        Delete expired memory blocks.

        Returns:
            Number of rows deleted
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "DELETE FROM session_memory_blocks WHERE expires_at < ?",
                (datetime.now().isoformat(),),
            )
            await db.commit()
            return cursor.rowcount

    async def cleanup_closed_sessions(self, days: int = 30) -> int:
        """
        Delete closed sessions older than N days.

        Args:
            days: Delete sessions closed more than this many days ago

        Returns:
            Number of rows deleted
        """
        if not self._initialized:
            await self.initialize()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                """
                DELETE FROM sessions
                WHERE status = 'closed' AND last_accessed < ?
                """,
                (cutoff,),
            )
            await db.commit()
            return cursor.rowcount

    async def get_stats(self) -> dict[str, int]:
        """Get storage statistics for dashboard."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(str(self.db_path)) as db:
            # Count active sessions
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sessions WHERE status = 'active'"
            )
            active_sessions = (await cursor.fetchone())[0]

            # Count total facts
            cursor = await db.execute("SELECT COUNT(*) FROM session_facts")
            total_facts = (await cursor.fetchone())[0]

            # Count total memory blocks
            cursor = await db.execute(
                "SELECT COUNT(*) FROM session_memory_blocks"
            )
            total_blocks = (await cursor.fetchone())[0]

            # Count closed sessions
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sessions WHERE status = 'closed'"
            )
            closed_sessions = (await cursor.fetchone())[0]

        return {
            "active_sessions": active_sessions,
            "total_facts": total_facts,
            "total_blocks": total_blocks,
            "closed_sessions": closed_sessions,
        }


# Global session storage instance
_session_storage: SessionStorage | None = None


def get_session_storage(
    db_path: Path | None = None,
) -> SessionStorage:
    """Get or create the global session storage instance."""
    global _session_storage
    if _session_storage is None:
        _session_storage = SessionStorage(db_path)
    return _session_storage
