"""
Client Configuration Generators.

Generates configuration files for connecting applications to AgentHub:
- Claude Desktop: claude_desktop_config.json
- VS Code: .vscode/mcp.json and tasks.json
- Raycast: Custom script for MCP queries
"""

import json
import os
from pathlib import Path
from typing import Any


def generate_claude_desktop_config(
    router_host: str = "localhost",
    router_port: int = 9090,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate Claude Desktop configuration for AgentHub.

    This uses the curl-based proxy mode where Claude sends MCP requests
    to curl, which forwards them to the AgentHub router.

    Args:
        router_host: AgentHub router host
        router_port: AgentHub router port
        output_path: If provided, write config to this path

    Returns:
        Configuration dictionary
    """
    config = {
        "mcpServers": {
            "agenthub": {
                "command": "curl",
                "args": [
                    "-s",
                    "-X",
                    "POST",
                    f"http://{router_host}:{router_port}/mcp/context7/tools/call",
                    "-H",
                    "Content-Type: application/json",
                    "-H",
                    "X-Client-Name: claude-desktop",
                    "-d",
                    "@-",
                ],
                "env": {},
            }
        }
    }

    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config, f, indent=2)

    return config


def generate_vscode_config(
    router_host: str = "localhost",
    router_port: int = 9090,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate VS Code MCP configuration for AgentHub.

    Creates .vscode/mcp.json in the specified workspace.

    Args:
        router_host: AgentHub router host
        router_port: AgentHub router port
        workspace_path: Workspace root (creates .vscode/mcp.json)

    Returns:
        Configuration dictionary
    """
    config = {
        "mcp.servers": {
            "agenthub": {
                "type": "http",
                "url": f"http://{router_host}:{router_port}",
                "headers": {"X-Client-Name": "vscode"},
            }
        }
    }

    if workspace_path:
        path = Path(workspace_path) / ".vscode" / "mcp.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config, f, indent=2)

    return config


def generate_vscode_tasks(
    router_host: str = "localhost",
    router_port: int = 9090,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate VS Code tasks.json for AgentHub pipelines.

    Creates tasks for:
    - Document Workspace: Generate docs for current project
    - MCP Query: Send a query to Sequential Thinking

    Args:
        router_host: AgentHub router host
        router_port: AgentHub router port
        workspace_path: Workspace root (creates .vscode/tasks.json)

    Returns:
        Tasks configuration dictionary
    """
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "AgentHub: Document Workspace",
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
                "label": "AgentHub: Health Check",
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
                "label": "AgentHub: List Servers",
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

        with open(path, "w") as f:
            json.dump(tasks, f, indent=2)

    return tasks


def generate_raycast_script(
    router_host: str = "localhost",
    router_port: int = 9090,
    output_path: str | None = None,
) -> str:
    """
    Generate Raycast script for MCP queries.

    Creates a Raycast script command that sends queries to AgentHub's
    Sequential Thinking server.

    Args:
        router_host: AgentHub router host
        router_port: AgentHub router port
        output_path: Script output path (default: ~/.config/raycast/scripts/)

    Returns:
        Script content
    """
    script = f'''#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title MCP Query
# @raycast.mode fullOutput
# @raycast.packageName AgentHub
# @raycast.icon brain

# Optional parameters:
# @raycast.argument1 {{ "type": "text", "placeholder": "Query" }}

# Documentation:
# @raycast.description Send a query to AgentHub Sequential Thinking
# @raycast.author AgentHub
# @raycast.authorURL https://github.com/yourusername/agenthub

ROUTER_HOST="{router_host}"
ROUTER_PORT="{router_port}"
QUERY="$1"

# Send to Sequential Thinking server
curl -s -X POST "http://$ROUTER_HOST:$ROUTER_PORT/mcp/sequential-thinking/tools/call" \\
  -H "Content-Type: application/json" \\
  -H "X-Client-Name: raycast" \\
  -d "{{
    \\"jsonrpc\\": \\"2.0\\",
    \\"method\\": \\"tools/call\\",
    \\"params\\": {{
      \\"name\\": \\"sequentialthinking\\",
      \\"arguments\\": {{
        \\"thought\\": \\"$QUERY\\",
        \\"thoughtNumber\\": 1,
        \\"totalThoughts\\": 3,
        \\"nextThoughtNeeded\\": true
      }}
    }},
    \\"id\\": 1
  }}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data:
        result = data['result']
        if isinstance(result, dict) and 'content' in result:
            for item in result['content']:
                if 'text' in item:
                    print(item['text'])
        else:
            print(json.dumps(result, indent=2))
    elif 'error' in data:
        print(f\\"Error: {{data['error'].get('message', 'Unknown error')}}\\")
    else:
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f\\"Parse error: {{e}}\\")
"
'''

    if output_path:
        path = Path(output_path).expanduser()
        if path.is_dir():
            path = path / "mcp-query.sh"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(script)
        os.chmod(path, 0o755)

    return script


def generate_obsidian_config(
    router_host: str = "localhost",
    router_port: int = 9090,
    vault_path: str = "~/Obsidian",
) -> dict[str, Any]:
    """
    Generate Obsidian MCP plugin configuration.

    Note: This is for reference. Actual Obsidian setup depends on the
    specific MCP plugin being used.

    Args:
        router_host: AgentHub router host
        router_port: AgentHub router port
        vault_path: Obsidian vault path

    Returns:
        Configuration dictionary for reference
    """
    return {
        "mcp_endpoint": f"http://{router_host}:{router_port}",
        "client_name": "obsidian",
        "default_vault_path": vault_path,
        "auto_link": True,
        "headers": {"X-Client-Name": "obsidian"},
    }
