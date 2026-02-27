"""Health and circuit breaker endpoints."""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)


def create_health_router(
    get_supervisor: Callable[[], Any],
    get_registry: Callable[[], Any],
    get_enhancement_service: Callable[[], Any],
    get_circuit_breakers: Callable[[], Any],
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health_check():
        """Health check endpoint - returns status of all services."""
        sup = get_supervisor()
        svc = get_enhancement_service()
        server_summary = sup.get_status_summary() if sup else {}

        ollama_status = "unknown"
        cache_stats = {}
        if svc:
            stats = await svc.get_stats()
            ollama_status = "up" if stats.get("ollama_healthy") else "down"
            cache_stats = stats.get("cache", {})

        return {
            "status": "healthy",
            "services": {
                "router": "up",
                "ollama": ollama_status,
                "cache": {
                    "status": "up",
                    "hit_rate": cache_stats.get("hits", 0)
                    / max(1, cache_stats.get("hits", 0) + cache_stats.get("misses", 0)),
                    "size": cache_stats.get("size", 0),
                },
            },
            "servers": server_summary,
        }

    @router.get("/health/{server}")
    async def server_health(server: str):
        """Health check for a specific MCP server."""
        reg = get_registry()
        cbs = get_circuit_breakers()
        if not reg:
            raise HTTPException(503, "Server registry not initialized")

        state = reg.get_state(server)
        if not state:
            raise HTTPException(404, f"Server {server} not found")

        cb_stats = None
        if cbs:
            breaker = cbs.get(server)
            cb_stats = breaker.stats.model_dump()

        return {
            "server": server,
            "status": state.process.status.value,
            "pid": state.process.pid,
            "restart_count": state.process.restart_count,
            "last_error": state.process.last_error,
            "circuit_breaker": cb_stats,
            "config": {
                "package": state.config.package,
                "transport": state.config.transport.value,
                "auto_start": state.config.auto_start,
            },
        }

    @router.get("/circuit-breakers")
    async def list_circuit_breakers():
        """Get all circuit breaker states."""
        cbs = get_circuit_breakers()
        if not cbs:
            raise HTTPException(503, "Circuit breakers not initialized")
        return cbs.get_all_stats()

    @router.post("/circuit-breakers/{name}/reset")
    async def reset_circuit_breaker(name: str):
        """Reset a specific circuit breaker."""
        cbs = get_circuit_breakers()
        if not cbs:
            raise HTTPException(503, "Circuit breakers not initialized")
        if cbs.reset(name):
            return {"message": f"Circuit breaker {name} reset"}
        raise HTTPException(404, f"Circuit breaker {name} not found")

    return router
