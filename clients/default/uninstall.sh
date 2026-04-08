#!/usr/bin/env bash
set -euo pipefail

# ── Client Uninstall Template ──────────────────────────────
#
# Reverses setup.sh: removes the symlink and restores any
# backup that was created during setup.
#
# Usage:
#   ./clients/<name>/uninstall.sh          # remove symlink
#   ./clients/<name>/uninstall.sh --purge  # also delete backup

# ── Customize these (must match setup.sh) ──────────────────

CLIENT_NAME="default"
CONFIG_FILE="mcp.json"
APP_CONFIG="$HOME/.prompthub/clients/$CLIENT_NAME/mcp.json"

# ── No changes needed below ────────────────────────────────

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
