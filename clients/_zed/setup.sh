#!/usr/bin/env bash
set -euo pipefail

# ── Zed setup ────────────────────────────────────────────────
# Strategy: manual (shared editor settings, JSONC format)
# Source:   clients/zed/settings.json (reference copy)
# Target:   ~/.config/zed/settings.json
#
# Zed's settings.json uses JSONC (comments + trailing commas)
# and contains editor-wide config (fonts, themes, keymaps).
# Cannot symlink — paste the context_servers block manually.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_CONFIG="$HOME/.config/zed/settings.json"

echo "── Zed MCP Setup ──────────────────────────────"
echo ""
echo "Reference: $SCRIPT_DIR/settings.json"
echo "Target:    $APP_CONFIG"
echo ""

if [ -f "$APP_CONFIG" ]; then
    echo "STATUS  target file exists"
    if grep -q "context_servers" "$APP_CONFIG" 2>/dev/null; then
        echo "STATUS  context_servers block found"
    else
        echo "STATUS  context_servers block NOT found — needs setup"
    fi
else
    echo "STATUS  target file not found"
fi

echo ""
echo "Add this block to your Zed settings.json:"
echo ""
cat <<'SNIPPET'
  "context_servers": {
    "prompthub": {
      "enabled": true,
      "remote": false,
      "command": "node",
      "args": ["~/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "AUTHORIZATION": "Bearer <your-key>",
        "CLIENT_NAME": "zed",
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "SERVERS": "memory,context7,sequential-thinking,desktop-commander"
      }
    }
  }
SNIPPET
echo ""
echo "Open Zed settings: cmd+, or 'zed: open settings' from command palette."
