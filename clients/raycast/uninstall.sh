#!/usr/bin/env bash
set -euo pipefail

# ── Raycast uninstall ───────────────────────────────────────
# Reverses setup.sh: removes symlink and restores backup.
# Usage:
#   ./clients/raycast/uninstall.sh          # remove symlink
#   ./clients/raycast/uninstall.sh --purge  # also delete backup

CLIENT_NAME="raycast"
CONFIG_FILE="mcp.json"
APP_CONFIG="$HOME/.config/raycast/mcp.json"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/$CONFIG_FILE"
PURGE=false

if [ "${1:-}" = "--purge" ]; then
    PURGE=true
fi

echo "── $CLIENT_NAME uninstall ──"

# Not a symlink — refuse to delete a real file
if [ -f "$APP_CONFIG" ] && [ ! -L "$APP_CONFIG" ]; then
    echo "SKIP  $APP_CONFIG is a regular file, not a symlink — leaving it alone"
    exit 0
fi

# Not our symlink — refuse to remove someone else's link
if [ -L "$APP_CONFIG" ] && [ "$(readlink "$APP_CONFIG")" != "$REPO_CONFIG" ]; then
    echo "SKIP  $APP_CONFIG points elsewhere ($(readlink "$APP_CONFIG")) — leaving it alone"
    exit 0
fi

# Remove the symlink
if [ -L "$APP_CONFIG" ]; then
    rm "$APP_CONFIG"
    echo "GONE  removed symlink $APP_CONFIG"
else
    echo "OK    no symlink found at $APP_CONFIG"
fi

# Restore backup if one exists
if [ -f "$APP_CONFIG.bak" ]; then
    if [ "$PURGE" = true ]; then
        rm "$APP_CONFIG.bak"
        echo "PURGE deleted backup $APP_CONFIG.bak"
    else
        mv "$APP_CONFIG.bak" "$APP_CONFIG"
        echo "BACK  restored $APP_CONFIG from backup"
    fi
fi
