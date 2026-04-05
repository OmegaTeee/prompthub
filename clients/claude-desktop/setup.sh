#!/usr/bin/env bash
set -euo pipefail

# ── Claude Desktop setup ────────────────────────────────────
# Strategy: symlink (full config including preferences)
# Source:   clients/claude-desktop/mcp.json
# Target:   ~/Library/Application Support/Claude/claude_desktop_config.json
#
# Note: This file includes both mcpServers and preferences.
# Edit clients/claude-desktop/mcp.json to change either.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/mcp.json"
APP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [ ! -f "$REPO_CONFIG" ]; then
    echo "FAIL  missing $REPO_CONFIG"
    exit 1
fi

# Already linked correctly?
if [ -L "$APP_CONFIG" ] && [ "$(readlink "$APP_CONFIG")" = "$REPO_CONFIG" ]; then
    echo "OK    already linked: $APP_CONFIG -> $REPO_CONFIG"
    exit 0
fi

# Back up existing regular file
if [ -f "$APP_CONFIG" ] && [ ! -L "$APP_CONFIG" ]; then
    cp "$APP_CONFIG" "$APP_CONFIG.bak"
    echo "BACK  saved $APP_CONFIG.bak"
fi

mkdir -p "$(dirname "$APP_CONFIG")"
ln -sfn "$REPO_CONFIG" "$APP_CONFIG"
echo "LINK  $APP_CONFIG -> $REPO_CONFIG"
