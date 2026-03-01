"""
Tool registry router with REST API endpoints.

Provides tool cache management endpoints under /tools prefix.
"""

import logging
from collections.abc import Callable

from fastapi import APIRouter, HTTPException

from .models import (
    ToolRegistryStats,
    ToolSnapshot,
    ToolSnapshotSummary,
)
from .storage import ToolRegistryStorage

logger = logging.getLogger(__name__)


def create_tool_registry_router(
    get_registry: Callable[[], ToolRegistryStorage],
    get_supervisor: Callable[[], object] | None = None,
) -> APIRouter:
    """
    Factory function to create tool registry router.

    Args:
        get_registry: Callable that returns ToolRegistryStorage instance
        get_supervisor: Optional callable for force-refresh (proxies to live server)

    Returns:
        APIRouter configured with /tools endpoints
    """
    router = APIRouter(prefix="/tools", tags=["tools"])

    # GET /tools — List all cached servers
    @router.get("")
    async def list_cached_servers() -> list[ToolSnapshotSummary]:
        """List all cached tool snapshots (summaries only)."""
        reg = get_registry()
        snapshots = await reg.get_all_cached()
        return [ToolSnapshotSummary(**s) for s in snapshots]

    # GET /tools/stats — Registry statistics
    @router.get("/stats", response_model=ToolRegistryStats)
    async def get_stats() -> ToolRegistryStats:
        """Get aggregate tool registry statistics."""
        reg = get_registry()
        stats = await reg.get_stats()
        return ToolRegistryStats(**stats)

    # GET /tools/{server} — Get cached tools for a server (full snapshot)
    @router.get("/{server}", response_model=ToolSnapshot)
    async def get_server_tools(server: str) -> ToolSnapshot:
        """Get full cached tool snapshot for a server (raw, pre-minification)."""
        reg = get_registry()
        snapshot = await reg.get_snapshot(server)

        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"No cached tools for server '{server}'",
            )

        return ToolSnapshot(**snapshot)

    # POST /tools/{server}/refresh — Force re-fetch from live server
    @router.post("/{server}/refresh")
    async def refresh_server_tools(server: str) -> dict:
        """
        Invalidate cache and re-fetch tools from the live MCP server.

        Requires the server to be running.
        """
        reg = get_registry()

        if not get_supervisor:
            raise HTTPException(
                status_code=503,
                detail="Supervisor not available for live refresh",
            )

        sup = get_supervisor()
        if not sup:
            raise HTTPException(503, "Supervisor not initialized")

        bridge = sup.get_bridge(server)
        if not bridge:
            raise HTTPException(
                status_code=503,
                detail=f"Server '{server}' is not running",
            )

        # Invalidate existing cache
        await reg.invalidate(server)

        # Fetch fresh tools from live server
        try:
            response = await bridge.send("tools/list", {}, timeout=30.0)

            tools = []
            if isinstance(response, dict):
                result = response.get("result", {})
                if isinstance(result, dict):
                    tools = result.get("tools", [])

            snapshot = await reg.cache_tools(server, tools)

            return {
                "status": "refreshed",
                "server": server,
                "tool_count": snapshot["tool_count"],
                "raw_size_bytes": snapshot["raw_size_bytes"],
            }

        except Exception as e:
            logger.error("Failed to refresh tools for %s: %s", server, e)
            raise HTTPException(
                status_code=503,
                detail=f"Failed to fetch tools from '{server}': {e}",
            )

    # DELETE /tools/{server} — Clear cache for a server
    @router.delete("/{server}")
    async def clear_server_cache(server: str) -> dict:
        """Clear cached tools for a server (archives before deleting)."""
        reg = get_registry()
        deleted = await reg.invalidate(server)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"No cached tools for server '{server}'",
            )

        return {"status": "cleared", "server": server}

    # POST /tools/archive — Archive expired snapshots
    @router.post("/archive")
    async def archive_expired() -> dict:
        """Move expired cache entries to archive table."""
        reg = get_registry()
        count = await reg.archive_expired()
        return {"status": "archived", "count": count}

    # POST /tools/cleanup — Clean up old archived snapshots
    @router.post("/cleanup")
    async def cleanup_archive(retention_days: int = 90) -> dict:
        """Delete archived snapshots older than retention period."""
        reg = get_registry()
        count = await reg.cleanup_archive(retention_days=retention_days)
        await reg.vacuum()
        return {"status": "cleaned", "deleted": count, "retention_days": retention_days}

    return router
