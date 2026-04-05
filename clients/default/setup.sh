#!/usr/bin/env bash
set -euo pipefail

# ── Client Setup Template ──────────────────────────────────
#
# Copy this script to a new clients/<name>/ directory and
# customize the variables below.
#
# Strategy: symlink
#   Creates a symlink from the app's config location to the
#   repo's config file. Backs up any existing file first.
#
# Usage:
#   ./clients/<name>/setup.sh          # install
#   ./clients/<name>/uninstall.sh      # reverse

# ── Customize these ────────────────────────────────────────

CLIENT_NAME="default"

# Config file in this directory (source of truth)
CONFIG_FILE="mcp.json"

# Where the app expects the config (symlink target)
# Examples:
#   "$HOME/.lmstudio/mcp.json"
#   "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
#   "$HOME/.config/zed/settings.json"
APP_CONFIG="$HOME/.prompthub/clients/$CLIENT_NAME/mcp.json"

# ── No changes needed below ────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/$CONFIG_FILE"

echo "── $CLIENT_NAME setup ──"

# Source exists?
if [ ! -f "$REPO_CONFIG" ]; then
    echo "FAIL  missing $REPO_CONFIG"
    exit 1
fi

# Already linked correctly?
if [ -L "$APP_CONFIG" ] && [ "$(readlink "$APP_CONFIG")" = "$REPO_CONFIG" ]; then
    echo "OK    already linked: $APP_CONFIG"
    exit 0
fi

# Back up existing regular file (not a symlink)
if [ -f "$APP_CONFIG" ] && [ ! -L "$APP_CONFIG" ]; then
    cp "$APP_CONFIG" "$APP_CONFIG.bak"
    echo "BACK  saved $APP_CONFIG.bak"
fi

# Create parent directory and symlink
mkdir -p "$(dirname "$APP_CONFIG")"
ln -sfn "$REPO_CONFIG" "$APP_CONFIG"
echo "LINK  $APP_CONFIG -> $REPO_CONFIG"
