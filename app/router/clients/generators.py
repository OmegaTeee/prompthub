"""
Client Configuration Generators.

Generates configuration files for connecting applications to PromptHub:
- Claude Desktop, VS Code, Cursor, Raycast: Bridge-based MCP configs
- VS Code tasks: Pipeline integration tasks

Bridge-based configs delegate to cli.generator for path-safe generation.
"""

import json
import os
from pathlib import Path
from typing import Any

from cli.generator import ConfigGenerator
from cli.models import ClientType
from cli.profiles import ProfileLoader


def generate_claude_desktop_config(
    router_host: str = "127.0.0.1",
    router_port: int = 9090,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate Claude Desktop configuration for PromptHub.

    Uses the Node.js bridge (prompthub-bridge.js) with path-safe generation.

    Args:
        router_host: PromptHub router host (default: 127.0.0.1)
        router_port: PromptHub router port
        output_path: If provided, write config to this path

    Returns:
        Configuration dictionary
    """
    gen = ConfigGenerator(router_url=f"http://{router_host}:{router_port}")
    loader = ProfileLoader()
    profile = loader.load(ClientType.claude_desktop)
    config = gen.generate(ClientType.claude_desktop, profile=profile)

    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2) + "\n")

    return config


def generate_vscode_config(
    router_host: str = "127.0.0.1",
    router_port: int = 9090,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate VS Code MCP configuration for PromptHub.

    Uses the Node.js bridge with VS Code-specific JSON structure.

    Args:
        router_host: PromptHub router host
        router_port: PromptHub router port
        workspace_path: Workspace root (creates .vscode/mcp.json)

    Returns:
        Configuration dictionary
    """
    gen = ConfigGenerator(router_url=f"http://{router_host}:{router_port}")
    loader = ProfileLoader()
    profile = loader.load(ClientType.vscode)
    config = gen.generate(ClientType.vscode, profile=profile)

    if workspace_path:
        path = Path(workspace_path) / ".vscode" / "mcp.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2) + "\n")

    return config


def generate_vscode_tasks(
    router_host: str = "127.0.0.1",
    router_port: int = 9090,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate VS Code tasks.json for PromptHub pipelines.

    Creates tasks for:
    - Document Workspace: Generate docs for current project
    - Health Check: Verify PromptHub router status
    - List Servers: Show running MCP servers

    Args:
        router_host: PromptHub router host
        router_port: PromptHub router port
        workspace_path: Workspace root (creates .vscode/tasks.json)

    Returns:
        Tasks configuration dictionary
    """
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "PromptHub: Document Workspace",
                "type": "shell",
                "command": "curl",
                "args": [
                    "-s",
                    "-X",
                    "POST",
                    f"http://{router_host}:{router_port}/pipelines/documentation",
                    "-H",
                    "Content-Type: application/json",
                    "-d",
                    '{"repo_path": "${workspaceFolder}", "project_name": "${workspaceFolderBasename}"}',
                ],
                "presentation": {"reveal": "always", "panel": "new"},
                "problemMatcher": [],
            },
            {
                "label": "PromptHub: Health Check",
                "type": "shell",
                "command": "curl",
                "args": [
                    "-s",
                    f"http://{router_host}:{router_port}/health",
                    "|",
                    "python3",
                    "-m",
                    "json.tool",
                ],
                "presentation": {"reveal": "always", "panel": "shared"},
                "problemMatcher": [],
            },
            {
                "label": "PromptHub: List Servers",
                "type": "shell",
                "command": "curl",
                "args": [
                    "-s",
                    f"http://{router_host}:{router_port}/servers",
                    "|",
                    "python3",
                    "-m",
                    "json.tool",
                ],
                "presentation": {"reveal": "always", "panel": "shared"},
                "problemMatcher": [],
            },
        ],
    }

    if workspace_path:
        path = Path(workspace_path) / ".vscode" / "tasks.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        # Merge with existing tasks if present
        if path.exists():
            with open(path) as f:
                existing = json.load(f)
            # Add new tasks, avoid duplicates by label
            existing_labels = {t["label"] for t in existing.get("tasks", [])}
            for task in tasks["tasks"]:
                if task["label"] not in existing_labels:
                    existing.setdefault("tasks", []).append(task)
            tasks = existing

        path.write_text(json.dumps(tasks, indent=2) + "\n")

    return tasks


def generate_raycast_config(
    router_host: str = "127.0.0.1",
    router_port: int = 9090,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate Raycast MCP configuration for PromptHub.

    Uses the Node.js bridge with Raycast-specific settings.

    Args:
        router_host: PromptHub router host
        router_port: PromptHub router port
        output_path: If provided, write config to this path

    Returns:
        Configuration dictionary
    """
    gen = ConfigGenerator(router_url=f"http://{router_host}:{router_port}")
    loader = ProfileLoader()
    profile = loader.load(ClientType.raycast)
    config = gen.generate(ClientType.raycast, profile=profile)

    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2) + "\n")

    return config
