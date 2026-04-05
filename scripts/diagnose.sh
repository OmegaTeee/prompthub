#!/usr/bin/env bash
set -euo pipefail

# ── PromptHub Diagnostics ────────────────────────────────────
# Replaces: python -m cli diagnose
# Checks: node, bridge, router, servers, client configs

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRIDGE="$REPO_ROOT/mcps/prompthub-bridge.js"
ROUTER_URL="http://127.0.0.1:9090"

PASS=0
FAIL=0
TOTAL=0

check() {
    local name="$1" passed="$2" msg="$3" details="${4:-}"
    TOTAL=$((TOTAL + 1))
    if [ "$passed" = "true" ]; then
        PASS=$((PASS + 1))
        printf "  [PASS] %-20s %s\n" "$name" "$msg"
    else
        FAIL=$((FAIL + 1))
        printf "  [FAIL] %-20s %s\n" "$name" "$msg"
    fi
    if [ -n "$details" ]; then
        printf "  %26s %s\n" "" "$details"
    fi
}

# ── 1. Node.js ───────────────────────────────────────────────

if command -v node > /dev/null 2>&1; then
    NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
    NODE_PATH=$(command -v node)
    check "Node.js" "true" "$NODE_VERSION" "Path: $NODE_PATH"
else
    check "Node.js" "false" "not found on PATH" "Install: https://nodejs.org/"
fi

# ── 2. Bridge file ───────────────────────────────────────────

if [ -f "$BRIDGE" ] && [ -r "$BRIDGE" ]; then
    BRIDGE_SIZE=$(wc -c < "$BRIDGE" | tr -d ' ')
    check "Bridge file" "true" "found (${BRIDGE_SIZE} bytes)" "Path: $BRIDGE"
else
    check "Bridge file" "false" "not found" "Expected: $BRIDGE"
fi

# ── 3. Router health ────────────────────────────────────────

HEALTH=$(curl -sf "$ROUTER_URL/health" 2>/dev/null || echo "")
if [ -n "$HEALTH" ]; then
    STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
    check "Router" "true" "healthy (status=$STATUS)" "URL: $ROUTER_URL"
else
    check "Router" "false" "unreachable" "URL: $ROUTER_URL"
fi

# ── 4. MCP servers ──────────────────────────────────────────

SERVERS_JSON=$(curl -sf "$ROUTER_URL/servers" 2>/dev/null || echo "")
if [ -n "$SERVERS_JSON" ]; then
    # Parse server names and statuses
    RUNNING=$(echo "$SERVERS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
servers = data.get('servers', {})
if isinstance(servers, dict):
    running = [k for k, v in servers.items() if isinstance(v, dict) and v.get('status') == 'running']
else:
    running = [s['name'] for s in servers if s.get('status') == 'running']
print(f'{len(running)} running: {\", \".join(running)}')
" 2>/dev/null || echo "parse error")
    check "Servers" "true" "$RUNNING"
else
    check "Servers" "false" "could not fetch server list"
fi

# ── 5. Client configs ───────────────────────────────────────

CLIENTS_DIR="$REPO_ROOT/clients"
CLIENT_CHECKS=0

for setup in "$CLIENTS_DIR"/*/setup.sh; do
    [ -f "$setup" ] || continue
    CLIENT_NAME=$(basename "$(dirname "$setup")")

    # Extract APP_CONFIG from the script header
    APP_CONFIG=$(grep '^APP_CONFIG=' "$setup" 2>/dev/null | head -1 | sed 's/APP_CONFIG=//' | tr -d '"' || echo "")

    # Skip informational scripts (no APP_CONFIG or uses $HOME in complex way)
    [ -z "$APP_CONFIG" ] && continue

    # Expand $HOME
    APP_CONFIG=$(echo "$APP_CONFIG" | sed "s|\$HOME|$HOME|g; s|\${HOME}|$HOME|g")

    # Also expand $REPO_ROOT references
    APP_CONFIG=$(echo "$APP_CONFIG" | sed "s|\$REPO_ROOT|$REPO_ROOT|g; s|\${REPO_ROOT}|$REPO_ROOT|g")

    # Skip if it still has unexpanded variables
    echo "$APP_CONFIG" | grep -q '\$' && continue

    CLIENT_CHECKS=$((CLIENT_CHECKS + 1))

    if [ -L "$APP_CONFIG" ]; then
        TARGET=$(readlink "$APP_CONFIG")
        # Check symlink points into our clients/ dir
        if echo "$TARGET" | grep -q "$CLIENTS_DIR"; then
            check "$CLIENT_NAME" "true" "symlink OK" "-> $TARGET"
        else
            check "$CLIENT_NAME" "true" "symlink (external)" "-> $TARGET"
        fi
    elif [ -f "$APP_CONFIG" ]; then
        check "$CLIENT_NAME" "true" "config file exists" "Path: $APP_CONFIG"
    else
        check "$CLIENT_NAME" "false" "config not found" "Expected: $APP_CONFIG"
    fi
done

if [ "$CLIENT_CHECKS" -eq 0 ]; then
    check "Client configs" "false" "no setup.sh scripts found"
fi

# ── Summary ─────────────────────────────────────────────────

echo ""
echo "  $PASS/$TOTAL checks passed"
[ "$FAIL" -gt 0 ] && exit 1
exit 0
