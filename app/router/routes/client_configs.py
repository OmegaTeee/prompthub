"""Client configuration generator endpoints."""

import logging

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from router.clients import (
    generate_claude_desktop_config,
    generate_raycast_script,
    generate_vscode_config,
    generate_vscode_tasks,
)
from router.config import get_settings

logger = logging.getLogger(__name__)


def create_client_configs_router() -> APIRouter:
    router = APIRouter(tags=["client-configs"])

    @router.get("/configs/claude-desktop")
    async def get_claude_desktop_config():
        """Generate Claude Desktop configuration for PromptHub."""
        settings = get_settings()
        return generate_claude_desktop_config(
            router_host="localhost",
            router_port=settings.port,
        )

    @router.get("/configs/vscode")
    async def get_vscode_config():
        """Generate VS Code MCP configuration for PromptHub."""
        settings = get_settings()
        return generate_vscode_config(
            router_host="localhost",
            router_port=settings.port,
        )

    @router.get("/configs/vscode-tasks")
    async def get_vscode_tasks():
        """Generate VS Code tasks.json for PromptHub pipelines."""
        settings = get_settings()
        return generate_vscode_tasks(
            router_host="localhost",
            router_port=settings.port,
        )

    @router.get("/configs/raycast")
    async def get_raycast_script():
        """Generate Raycast script for MCP queries."""
        settings = get_settings()
        script = generate_raycast_script(
            router_host="localhost",
            router_port=settings.port,
        )
        return PlainTextResponse(content=script, media_type="text/plain")

    return router
