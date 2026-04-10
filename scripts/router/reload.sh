#!/usr/bin/env bash
# Reload PromptHub router configuration without restarting.
# Usage: ./scripts/router/reload.sh [component]
#
# Components:
#   api-keys     Reload bearer tokens from api-keys.json
#   all          Reload all reloadable configs (default)
#
# Examples:
#   ./scripts/router/reload.sh              # reload everything
#   ./scripts/router/reload.sh api-keys     # just API keys

set -euo pipefail

ROUTER_URL="${PROMPTHUB_URL:-http://127.0.0.1:9090}"
COMPONENT="${1:-all}"

reload_api_keys() {
  echo "[reload] API keys from api-keys.json..."
  result=$(curl -sf -X POST "${ROUTER_URL}/v1/api-keys/reload" 2>&1) || {
    echo "[reload] FAILED — is the router running at ${ROUTER_URL}?"
    return 1
  }
  count=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count', '?'))" 2>/dev/null || echo "?")
  echo "[reload] OK — ${count} keys loaded"
}

case "$COMPONENT" in
  api-keys)
    reload_api_keys
    ;;
  all)
    reload_api_keys
    # Add future reloadable components here:
    # reload_enhancement_rules
    # reload_mcp_servers
    ;;
  *)
    echo "Unknown component: $COMPONENT"
    echo "Usage: $0 [api-keys|all]"
    exit 1
    ;;
esac
