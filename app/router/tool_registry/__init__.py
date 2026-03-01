"""
Tool registry for MCP tool definition caching and archival.

Provides:
- SQLite-backed tool definition cache
- Automatic archival of old snapshots
- REST API endpoints (/tools/*)
"""

from .models import (
    CachedTool,
    ToolRegistryStats,
    ToolSnapshot,
    ToolSnapshotSummary,
)
from .router import create_tool_registry_router
from .storage import ToolRegistryStorage, get_tool_registry

__all__ = [
    "ToolRegistryStorage",
    "get_tool_registry",
    "create_tool_registry_router",
    "CachedTool",
    "ToolSnapshot",
    "ToolSnapshotSummary",
    "ToolRegistryStats",
]
