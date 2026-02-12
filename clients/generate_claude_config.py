#!/usr/bin/env python3
"""
Generate comprehensive Claude Desktop configuration for AgentHub.

This script creates a claude_desktop_config.json that gives Claude Desktop
access to all MCP servers through the AgentHub router.
"""

import json
from pathlib import Path
import sys


def generate_comprehensive_claude_config(
    router_host: str = "localhost",
    router_port: int = 9090,
    output_path: str | None = None,
) -> dict:
    """
    Generate Claude Desktop configuration with all AgentHub MCP servers.

    Creates curl-based proxy configurations for each server, allowing
    Claude Desktop to access all MCP tools through AgentHub's router.
    """

    # MCP servers available through AgentHub
    servers = {
        "context7": {
            "description": "Documentation fetching from libraries",
            "endpoint": "context7",
        },
        "desktop-commander": {
            "description": "File operations and terminal commands",
            "endpoint": "desktop-commander",
        },
        "sequential-thinking": {
            "description": "Step-by-step reasoning and planning",
            "endpoint": "sequential-thinking",
        },
        "memory": {
            "description": "Cross-session context persistence",
            "endpoint": "memory",
        },
        "deepseek-reasoner": {
            "description": "Local reasoning without API costs",
            "endpoint": "deepseek-reasoner",
        },
        "fetch": {
            "description": "HTTP fetch and web content retrieval",
            "endpoint": "fetch",
        },
        "obsidian": {
            "description": "Semantic search and file management for Obsidian",
            "endpoint": "obsidian",
        },
    }

    config = {"mcpServers": {}}

    # Generate curl-based proxy for each server
    for name, info in servers.items():
        config["mcpServers"][f"agenthub-{name}"] = {
            "command": "curl",
            "args": [
                "-s",
                "-X",
                "POST",
                f"http://{router_host}:{router_port}/mcp/{info['endpoint']}/tools/call",
                "-H",
                "Content-Type: application/json",
                "-H",
                "X-Client-Name: claude-desktop",
                "-d",
                "@-",
            ],
            "env": {},
        }

    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration written to: {path}")
    else:
        print(json.dumps(config, indent=2))

    return config


def main():
    # Default Claude Desktop config path on macOS
    default_path = "~/Library/Application Support/Claude/claude_desktop_config.json"

    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = default_path

    print(f"Generating Claude Desktop configuration...")
    print(f"Router: http://localhost:9090")
    print(f"Output: {output_path}")
    print()

    config = generate_comprehensive_claude_config(
        router_host="localhost",
        router_port=9090,
        output_path=output_path,
    )

    print()
    print("✨ Configuration includes access to:")
    for server in config["mcpServers"].keys():
        print(f"  - {server}")

    print()
    print("📝 Next steps:")
    print("  1. Restart Claude Desktop")
    print("  2. Test MCP access with a command like:")
    print('     "Use the context7 tool to search for Python documentation"')
    print()


if __name__ == "__main__":
    main()
