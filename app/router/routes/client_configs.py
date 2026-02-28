"""Client configuration generator endpoints."""

import logging

from fastapi import APIRouter

from router.clients import (
    generate_claude_desktop_config,
    generate_raycast_config,
    generate_vscode_config,
    generate_vscode_tasks,
)
from router.config import get_settings

logger = logging.getLogger(__name__)


def create_client_configs_router() -> APIRouter:
    router = APIRouter(tags=["client-configs"])

    @router.get("/configs/claude-desktop")
    async def get_claude_desktop_config():
        """Generate Claude Desktop bridge configuration for PromptHub."""
        settings = get_settings()
        return generate_claude_desktop_config(
            router_host="127.0.0.1",
            router_port=settings.port,
        )

    @router.get("/configs/vscode")
    async def get_vscode_config():
        """Generate VS Code bridge configuration for PromptHub."""
        settings = get_settings()
        return generate_vscode_config(
            router_host="127.0.0.1",
            router_port=settings.port,
        )

    @router.get("/configs/vscode-tasks")
    async def get_vscode_tasks():
        """Generate VS Code tasks.json for PromptHub pipelines."""
        settings = get_settings()
        return generate_vscode_tasks(
            router_host="127.0.0.1",
            router_port=settings.port,
        )

    @router.get("/configs/raycast")
    async def get_raycast_config():
        """Generate Raycast bridge configuration for PromptHub."""
        settings = get_settings()
        return generate_raycast_config(
            router_host="127.0.0.1",
            router_port=settings.port,
        )

    return router
