#!/usr/bin/env bash
set -euo pipefail

# ── Codex setup ──────────────────────────────────────────────
# Strategy: manual (TOML config format)
# Source:   clients/codex/config.toml
# Target:   ~/.codex/config.toml
#
# Codex uses TOML, not JSON. Edit the config file directly.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/config.toml"
APP_CONFIG="$HOME/.codex/config.toml"

echo "── Codex MCP Setup ────────────────────────────"
echo ""
echo "Source:  $REPO_CONFIG"
echo "Target:  $APP_CONFIG"
echo ""

if [ -f "$APP_CONFIG" ]; then
    echo "STATUS  target file exists"
    if grep -q "prompthub" "$APP_CONFIG" 2>/dev/null; then
        echo "STATUS  prompthub entry found"
    else
        echo "STATUS  prompthub entry NOT found — needs setup"
    fi
else
    echo "STATUS  target file not found"
fi

echo ""
echo "Copy or merge the MCP server block from:"
echo "  $REPO_CONFIG"
echo ""
echo "Into your Codex config at:"
echo "  $APP_CONFIG"
echo ""
echo "TOML block to add:"
echo ""
cat "$REPO_CONFIG"
