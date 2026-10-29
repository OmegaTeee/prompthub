#!/usr/bin/env zsh

set -euo pipefail

echo "[PromptHub] Killing router (uvicorn)..."
pkill -f "uvicorn router.main:app" || echo "[PromptHub] No router process found"

echo "[PromptHub] Killing MCP bridge (prompthub-bridge.js)..."
pkill -f "prompthub-bridge.js" || echo "[PromptHub] No bridge process found"

echo "[PromptHub] Note: LM Studio is managed via its own GUI — close it separately if needed."

echo "[PromptHub] Done."
