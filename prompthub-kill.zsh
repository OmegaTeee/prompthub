#!/usr/bin/env zsh

set -euo pipefail

echo "[PromptHub] Killing router (uvicorn)..."
pkill -f "uvicorn router.main:app" || echo "[PromptHub] No router process found"

echo "[PromptHub] Killing MCP bridge (prompthub-bridge.js)..."
pkill -f "prompthub-bridge.js" || echo "[PromptHub] No bridge process found"

echo "[PromptHub] Optionally kill Ollama (local models)..."
echo "[PromptHub]   To stop Ollama as well, run:  killall ollama"

echo "[PromptHub] Done."
