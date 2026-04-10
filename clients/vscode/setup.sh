#!/usr/bin/env bash
set -euo pipefail

# ── VS Code setup ───────────────────────────────────────────
# Strategy: manual (shared editor settings file)
# Source:   clients/vscode/mcp.json
# Target:   ~/Library/AppSupport/Code/User/mcp.json
# AppSupport folder is symlinked to ~/Library/Application Support/Code, but we want to avoid symlinks for the config file itself.
#
# VS Code's config file contains other extension settings.
# Cannot symlink — merge the MCP servers block manually.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/mcp.json"
APP_CONFIG="$HOME/Library/Application Support/Code/User/settings/mcp.json"

echo "── VS Code MCP Setup ──────────────────────────"
echo ""
echo "Source:  $REPO_CONFIG"
echo "Target:  $APP_CONFIG"
echo ""

if [ -L "$SCRIPT_DIR/settings.json" ]; then
    echo "REF     settings.json -> $(readlink "$SCRIPT_DIR/settings.json")"
    echo ""
fi

if [ -f "$APP_CONFIG" ]; then
    echo "STATUS  target file exists"
else
    echo "STATUS  target file not found"
fi

echo ""
echo "VS Code shares its settings file with other extensions."
echo "Copy the 'servers' block from mcp.json into the target file:"
echo ""
echo "  cat $REPO_CONFIG"
echo ""
echo "Or use the VS Code MCP settings UI to add the servers."
