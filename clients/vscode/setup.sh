#!/usr/bin/env bash
set -euo pipefail

# VS Code setup
# Source: clients/vscode/mcp.json
# Target: ~/Library/Application Support/Code/User/mcp.json
# The Code user settings directory is symlinked, and the MCP config file
# itself is a symlink to the repo source of truth.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/mcp.json"
APP_CONFIG="$HOME/Library/Application Support/Code/User/mcp.json"

echo "── VS Code MCP Setup ──────────────────────────"
echo ""
echo "Source: $REPO_CONFIG"
echo "Target: $APP_CONFIG"
echo ""

if [ -L "$SCRIPT_DIR/settings.json" ]; then
  echo "REF settings.json -> $(readlink "$SCRIPT_DIR/settings.json")"
  echo ""
fi

if [ -f "$APP_CONFIG" ]; then
  echo "STATUS target file exists"
else
  echo "STATUS target file not found"
fi

echo ""
echo "VS Code stores MCP servers in the user-level mcp.json file."
echo "Copy the 'servers' block from mcp.json into the target file:"
echo ""
echo "  cat $REPO_CONFIG"
echo ""
echo "Or use the VS Code MCP settings UI to add servers."
