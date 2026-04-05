#!/usr/bin/env bash
set -euo pipefail

# ── Open WebUI setup ─────────────────────────────────────────
# Strategy: manual (HTTP connection, no MCP bridge)
# Source:   clients/open-webui/example.toml
# Target:   Open WebUI admin settings (web UI)
#
# Open WebUI connects to PromptHub via HTTP, not stdio bridge.
# Configure the connection in the Open WebUI admin panel.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXAMPLE="$SCRIPT_DIR/example.toml"

echo "── Open WebUI Setup ─────────────────────────────"
echo ""
echo "Reference: $EXAMPLE"
echo ""
echo "Open WebUI connects via HTTP (no bridge needed)."
echo "Configure in the admin panel:"
echo ""
echo "  1. Open WebUI > Admin > Settings > Connections"
echo "  2. Set OpenAI API URL:  http://127.0.0.1:9090/v1"
echo "  3. Set API Key:         sk-prompthub-openwebui-001"
echo "  4. Set MCP endpoint:    http://127.0.0.1:9090/mcp-direct/mcp"
echo ""
echo "See $EXAMPLE for full configuration details."
