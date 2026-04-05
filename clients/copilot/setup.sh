#!/usr/bin/env bash
set -euo pipefail

# ── GitHub Copilot setup ─────────────────────────────────────
# Strategy: manual (uses VS Code or project-level config)
# Source:   clients/copilot/mcp.json
# Target:   project-level .vscode/mcp.json or VS Code settings
#
# Copilot reads MCP config from VS Code's MCP settings or
# from a project-level .vscode/mcp.json file.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/mcp.json"

echo "── GitHub Copilot MCP Setup ─────────────────────"
echo ""
echo "Source:  $REPO_CONFIG"
echo ""
echo "Copilot reads MCP servers from VS Code settings."
echo "Add the mcpServers block to your project or user config:"
echo ""
echo "  Option A: Project-level .vscode/mcp.json"
echo "  Option B: VS Code user settings (settings.json)"
echo ""
echo "Config to add:"
echo ""
cat "$REPO_CONFIG"
