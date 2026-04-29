#!/usr/bin/env bash
set -euo pipefail

# ── cherry-studio setup ─────────────────────────────────────
# Strategy: manual (GUI-based config in LevelDB)
# Source:   clients/_cherry-studio/mcp-servers-example.json
# Target:   Cherry Studio > Settings > MCP Servers > Edit JSON
#
# cherry-studio stores its config in Electron LevelDB, not files.
# Paste the JSON via the GUI's "Edit JSON" dialog.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXAMPLE="$SCRIPT_DIR/mcp-servers-example.json"

echo "── cherry-studio MCP setup ─────────────────────"
echo ""
echo "Source:  $EXAMPLE"
echo ""

if [ -L "$SCRIPT_DIR/logs" ]; then
    echo "REF     logs -> $(readlink "$SCRIPT_DIR/logs")"
    echo ""
fi

echo "Cherry Studio stores MCP config in its internal database."
echo "To configure:"
echo ""
echo "  1. Open Cherry Studio > Settings > MCP Servers"
echo "  2. Click 'Edit JSON' button"
echo "  3. Paste the contents of:"
echo "     $EXAMPLE"
echo "  4. Save and restart Cherry Studio"
echo ""
echo "JSON to paste:"
echo ""
cat "$EXAMPLE"
