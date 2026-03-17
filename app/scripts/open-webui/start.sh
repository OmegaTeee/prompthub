#!/bin/bash
# start.sh — Start Open WebUI connected to PromptHub
#
# Prerequisites:
#   - Ollama running on port 11434
#   - PromptHub router running on port 9090
#   - uvx installed (pipx/uv)
#
# Usage:
#   ./start.sh              # Uses defaults from ~/.prompthub/open-webui.json
#   OWUI_PORT=8080 ./start.sh  # Override port

set -euo pipefail

CONFIG_FILE="${HOME}/.prompthub/open-webui.json"
LOG_FILE="${HOME}/.prompthub/open-webui.log"

# Defaults (overridden by config file or env vars)
OWUI_PORT="${OWUI_PORT:-3000}"
PROMPTHUB_URL="${PROMPTHUB_URL:-http://127.0.0.1:9090}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OWUI_API_KEY="${OWUI_API_KEY:-sk-prompthub-openwebui-001}"

# Read settings from config file if it exists
if [[ -f "$CONFIG_FILE" ]]; then
    CONFIG_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('open_webui', {}).get('port', ''))" 2>/dev/null || true)
    CONFIG_KEY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('open_webui', {}).get('api_key', ''))" 2>/dev/null || true)
    [[ -n "$CONFIG_PORT" ]] && OWUI_PORT="${OWUI_PORT:-$CONFIG_PORT}"
    [[ -n "$CONFIG_KEY" ]] && OWUI_API_KEY="${CONFIG_KEY}"
fi

echo "=== Open WebUI Startup ==="
echo "  Port:         $OWUI_PORT"
echo "  PromptHub:    $PROMPTHUB_URL"
echo "  API Base URL: ${PROMPTHUB_URL}/v1"
echo "  API Key:      ${OWUI_API_KEY:0:15}..."
echo "  Data Dir:     ~/.open-webui"
echo "  Log:          $LOG_FILE"
echo ""

# Check Ollama
if ! curl -sf "http://127.0.0.1:${OLLAMA_PORT}/" >/dev/null 2>&1; then
    echo "WARNING: Ollama not responding on port ${OLLAMA_PORT}"
    echo "  Open WebUI will start but model loading may fail."
    echo ""
fi

# Check PromptHub
if ! curl -sf "${PROMPTHUB_URL}/health" >/dev/null 2>&1; then
    echo "WARNING: PromptHub not responding at ${PROMPTHUB_URL}"
    echo "  Open WebUI will start but API proxy may fail."
    echo ""
fi

# Check if already running
if lsof -i :"$OWUI_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERROR: Port $OWUI_PORT already in use"
    lsof -i :"$OWUI_PORT" -sTCP:LISTEN
    exit 1
fi

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "Starting Open WebUI..."

# Export env vars that Open WebUI needs to connect to PromptHub
export DATA_DIR="${HOME}/.open-webui"
export ENABLE_OPENAI_API=true
export OPENAI_API_BASE_URL="${PROMPTHUB_URL}/v1"
export OPENAI_API_KEY="${OWUI_API_KEY}"

# Start Open WebUI via uvx (pin to compatible range)
exec uvx --python 3.11 "open-webui>=0.8,<0.8.10" serve \
    --port "$OWUI_PORT" \
    >> "$LOG_FILE" 2>&1
