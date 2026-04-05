#!/usr/bin/env bash
set -euo pipefail

# ── Claude Code setup ───────────────────────────────────────
# Strategy: symlink (project-level mcp.json at repo root)
# Source:   clients/claude-code/mcp.json
# Target:   <repo-root>/mcp.json
#
# Claude Code reads mcp.json from the project root.
# This script verifies the repo root file matches this config.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/mcp.json"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_CONFIG="$REPO_ROOT/mcp.json"

if [ ! -f "$REPO_CONFIG" ]; then
    echo "FAIL  missing $REPO_CONFIG"
    exit 1
fi

# Check if root mcp.json exists and matches
if [ -f "$APP_CONFIG" ]; then
    if diff -q "$REPO_CONFIG" "$APP_CONFIG" > /dev/null 2>&1; then
        echo "OK    $APP_CONFIG matches $REPO_CONFIG"
        exit 0
    else
        echo "WARN  $APP_CONFIG differs from $REPO_CONFIG"
        echo "      run: cp $REPO_CONFIG $APP_CONFIG"
        exit 1
    fi
fi

cp "$REPO_CONFIG" "$APP_CONFIG"
echo "COPY  $REPO_CONFIG -> $APP_CONFIG"
