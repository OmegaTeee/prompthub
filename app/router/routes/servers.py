"""Server management endpoints."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from router.servers import ServerConfig, ServerStatus, ServerTransport

logger = logging.getLogger(__name__)


class InstallServerRequest(BaseModel):
    """Request body for installing a new MCP server."""

    package: str
    name: str | None = None
    auto_start: bool = False
    description: str = ""


def create_servers_router(
    get_registry: Callable[[], Any],
    get_supervisor: Callable[[], Any],
    get_circuit_breakers: Callable[[], Any],
    rebuild_gateway: Callable[[], Coroutine[Any, Any, None]],
) -> APIRouter:
    router = APIRouter(tags=["servers"])

    @router.get("/servers")
    async def list_servers():
        """List all configured MCP servers with their status."""
        reg = get_registry()
        if not reg:
            raise HTTPException(503, "Server registry not initialized")

        states = reg.list_all()
        return {
            "servers": [
                {
                    "name": state.config.name,
                    "package": state.config.package,
                    "transport": state.config.transport.value,
                    "status": state.process.status.value,
                    "pid": state.process.pid,
                    "auto_start": state.config.auto_start,
                    "restart_count": state.process.restart_count,
                    "description": state.config.description,
                }
                for state in states
            ]
        }

    @router.get("/servers/{name}")
    async def get_server(name: str):
        """Get detailed information about a specific server."""
        reg = get_registry()
        if not reg:
            raise HTTPException(503, "Server registry not initialized")

        state = reg.get_state(name)
        if not state:
            raise HTTPException(404, f"Server {name} not found")

        return {
            "name": state.config.name,
            "config": state.config.model_dump(),
            "process": state.process.model_dump(),
        }

    @router.post("/servers/{name}/start")
    async def start_server(name: str):
        """Start a stopped server."""
        sup = get_supervisor()
        reg = get_registry()
        cbs = get_circuit_breakers()
        if not sup:
            raise HTTPException(503, "Supervisor not initialized")

        config = reg.get(name) if reg else None
        if not config:
            raise HTTPException(404, f"Server {name} not found")

        info = reg.get_process_info(name) if reg else None
        if info and info.status == ServerStatus.RUNNING:
            raise HTTPException(400, f"Server {name} is already running")

        try:
            await sup.start_server(name)
            if cbs:
                cbs.reset(name)
            return {"message": f"Server {name} started", "status": "running"}
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            raise HTTPException(500, f"Failed to start server: {e}")

    @router.post("/servers/{name}/stop")
    async def stop_server(name: str):
        """Stop a running server."""
        sup = get_supervisor()
        reg = get_registry()
        if not sup:
            raise HTTPException(503, "Supervisor not initialized")

        config = reg.get(name) if reg else None
        if not config:
            raise HTTPException(404, f"Server {name} not found")

        info = reg.get_process_info(name) if reg else None
        if not info or info.status != ServerStatus.RUNNING:
            raise HTTPException(400, f"Server {name} is not running")

        try:
            await sup.stop_server(name)
            return {"message": f"Server {name} stopped", "status": "stopped"}
        except Exception as e:
            logger.error(f"Failed to stop {name}: {e}")
            raise HTTPException(500, f"Failed to stop server: {e}")

    @router.post("/servers/{name}/restart")
    async def restart_server(name: str):
        """Restart a server."""
        sup = get_supervisor()
        reg = get_registry()
        cbs = get_circuit_breakers()
        if not sup:
            raise HTTPException(503, "Supervisor not initialized")

        config = reg.get(name) if reg else None
        if not config:
            raise HTTPException(404, f"Server {name} not found")

        try:
            await sup.restart_server(name)
            if cbs:
                cbs.reset(name)
            return {"message": f"Server {name} restarted", "status": "running"}
        except Exception as e:
            logger.error(f"Failed to restart {name}: {e}")
            raise HTTPException(500, f"Failed to restart server: {e}")

    @router.post("/servers/install")
    async def install_server(request: InstallServerRequest):
        """Install and configure a new MCP server."""
        reg = get_registry()
        if not reg:
            raise HTTPException(503, "Server registry not initialized")

        name = request.name or request.package.split("/")[-1].replace("@", "").replace(
            "-mcp", ""
        )

        if reg.get(name):
            raise HTTPException(400, f"Server {name} already exists")

        config = ServerConfig(
            name=name,
            package=request.package,
            transport=ServerTransport.STDIO,
            command="npx",
            args=["-y", request.package],
            auto_start=request.auto_start,
            description=request.description,
        )

        try:
            reg.add(config)
            await rebuild_gateway()
            return {
                "message": f"Server {name} installed",
                "name": name,
                "package": request.package,
            }
        except Exception as e:
            logger.error(f"Failed to install {name}: {e}")
            raise HTTPException(500, f"Failed to install server: {e}")

    @router.delete("/servers/{name}")
    async def remove_server(name: str):
        """Remove a server configuration."""
        reg = get_registry()
        if not reg:
            raise HTTPException(503, "Server registry not initialized")

        config = reg.get(name)
        if not config:
            raise HTTPException(404, f"Server {name} not found")

        info = reg.get_process_info(name)
        if info and info.status == ServerStatus.RUNNING:
            raise HTTPException(400, f"Cannot remove running server {name}, stop it first")

        try:
            reg.remove(name)
            await rebuild_gateway()
            return {"message": f"Server {name} removed"}
        except Exception as e:
            logger.error(f"Failed to remove {name}: {e}")
            raise HTTPException(500, f"Failed to remove server: {e}")

    return router
