#!/usr/bin/env zsh

set -euo pipefail

ROOT="$HOME/prompthub"
APP_DIR="$ROOT/app"
LOG_DIR="$ROOT/logs"

mkdir -p "$LOG_DIR"

echo "[PromptHub] Starting Ollama (if not already running)..."
if ! pgrep -x "ollama" >/dev/null 2>&1; then
  ollama serve >/dev/null 2>&1 &!
  sleep 2
fi

echo "[PromptHub] Activating venv..."
cd "$APP_DIR"
if [[ -f ".venv/bin/activate" ]]; then
  source .venv/bin/activate
else
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
fi

echo "[PromptHub] Starting router on 127.0.0.1:9090..."
# quiet stdout, send stderr to log
uvicorn router.main:app \
  --host 127.0.0.1 \
  --port 9090 \
  >>"$LOG_DIR/router-stdout.log" \
  2>>"$LOG_DIR/router-stderr.log" &
ROUTER_PID=$!

sleep 2

echo "[PromptHub] Health check..."
if ! curl -sSf "http://127.0.0.1:9090/health" >/dev/null; then
  echo "[PromptHub] Router health check FAILED, killing PID $ROUTER_PID"
  kill "$ROUTER_PID" || true
  exit 1
fi

echo "[PromptHub] OpenAI-compatible API test (models)..."
curl -s "http://127.0.0.1:9090/v1/models" \
  -H "Authorization: Bearer sk-prompthub-code-001" \
  | head -c 400 || true

echo "\n[PromptHub] Router is up (PID $ROUTER_PID). Tail logs with:"
echo "  tail -f \"$LOG_DIR/router-stderr.log\""

wait "$ROUTER_PID"
