#!/usr/bin/env bash
set -euo pipefail

# ── LM Studio setup ─────────────────────────────────────────
# Strategy: symlink (MCP-only config file)
# Source:   clients/lm-studio/mcp.json
# Target:   ~/.lmstudio/mcp.json

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/mcp.json"
APP_CONFIG="$HOME/.lmstudio/mcp.json"

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
