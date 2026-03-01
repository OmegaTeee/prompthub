"""
Pydantic models for tool registry requests/responses.
"""

from typing import Any

from pydantic import BaseModel


# Response Models
class CachedTool(BaseModel):
    """Single tool definition from a cached snapshot (MCP camelCase keys)."""

    name: str
    description: str | None = None
    inputSchema: dict[str, Any] | None = None
    annotations: dict[str, Any] | None = None


class ToolSnapshot(BaseModel):
    """Server-level tool snapshot (current cache entry)."""

    server_name: str
    tools: list[CachedTool]
    tool_count: int
    raw_size_bytes: int
    cached_at: str  # ISO 8601
    expires_at: str | None = None
    last_served: str | None = None
    serve_count: int = 0


class ToolSnapshotSummary(BaseModel):
    """Lightweight summary without full tool definitions."""

    server_name: str
    tool_count: int
    raw_size_bytes: int
    cached_at: str
    expires_at: str | None = None
    last_served: str | None = None
    serve_count: int = 0


class ToolRegistryStats(BaseModel):
    """Aggregate tool registry statistics."""

    cached_servers: int
    total_tools: int
    total_size_bytes: int
    total_serve_count: int
    oldest_snapshot: str | None = None  # ISO 8601
    newest_snapshot: str | None = None
    archived_snapshots: int = 0
