"""
Activity Logging for Dashboard.

Tracks recent requests with method, path, status, and duration.
Uses both in-memory deque (for quick access) and persistent SQLite storage.
"""

import logging
import time
from collections import deque
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Forward declaration for type hint
if False:  # TYPE_CHECKING
    pass


class ActivityEntry(BaseModel):
    """A single activity log entry."""

    timestamp: str
    method: str
    path: str
    status: int
    duration: float  # seconds


class ActivityLog:
    """
    Thread-safe activity log with bounded size.

    Stores the most recent N requests for dashboard display.
    Older entries are automatically evicted.
    """

    def __init__(self, max_entries: int = 100):
        """
        Initialize the activity log.

        Args:
            max_entries: Maximum number of entries to keep
        """
        self._entries: deque[ActivityEntry] = deque(maxlen=max_entries)
        self._max_entries = max_entries

    def add(
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
        entry = ActivityEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            method=method,
            path=path,
            status=status,
            duration=duration,
        )
        self._entries.append(entry)

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get most recent activity entries.

        Args:
            limit: Maximum entries to return

        Returns:
            List of activity entries (newest first)
        """
        entries = list(self._entries)[-limit:]
        return [e.model_dump() for e in reversed(entries)]

    def clear(self) -> None:
        """Clear all activity entries."""
        self._entries.clear()

    @property
    def size(self) -> int:
        """Current number of entries."""
        return len(self._entries)


# Global activity log instance
activity_log = ActivityLog(max_entries=100)


class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request activity.

    Captures method, path, status code, and duration for each request.
    Excludes dashboard partial requests to avoid noise.

    Writes to both:
    1. In-memory log (for quick dashboard access)
    2. Persistent SQLite log (for historical queries)
    """

    def __init__(
        self,
        app,
        log: ActivityLog | None = None,
    ):
        super().__init__(app)
        self._log = log or activity_log

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log activity."""
        # Skip logging for dashboard partials (they poll frequently)
        path = request.url.path
        if path.startswith("/dashboard/") and "-partial" in path:
            return await call_next(request)

        # Skip static files
        if path.startswith("/static/"):
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Write to in-memory log (synchronous)
        self._log.add(
            method=request.method,
            path=path,
            status=response.status_code,
            duration=duration,
        )

        # Write to persistent log (async, with context preservation)
        # Get persistent log lazily to avoid circular dependency
        try:
            from router.middleware.persistent_activity import persistent_activity_log

            if persistent_activity_log and persistent_activity_log._initialized:
                # Await directly to preserve context (SQLite writes are fast)
                await persistent_activity_log.add(
                    method=request.method,
                    path=path,
                    status=response.status_code,
                    duration=duration,
                )
        except Exception as e:
            # Don't fail request if activity logging fails
            logger.warning(f"Failed to write to persistent activity log: {e}")

        return response
