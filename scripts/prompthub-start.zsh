#!/usr/bin/env zsh

set -euo pipefail

ROOT="$HOME/prompthub"
APP_DIR="$ROOT/app"
LOG_DIR="$ROOT/logs"

mkdir -p "$LOG_DIR"

LLM_PORT="${LLM_PORT:-1234}"
echo "[PromptHub] Checking LLM server on port ${LLM_PORT}..."
if ! curl -sf "http://127.0.0.1:${LLM_PORT}/v1/models" > /dev/null 2>&1; then
  echo "[PromptHub] LLM server not responding on port ${LLM_PORT}"
  echo "[PromptHub]   Start LM Studio and enable the server in the Developer tab"
  exit 1
fi
echo "[PromptHub] LLM server healthy on port ${LLM_PORT}"

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

echo "[PromptHub] Waiting for startup..."
for i in {1..15}; do
  if curl -sSf "http://127.0.0.1:9090/health" >/dev/null 2>&1; then
    echo "[PromptHub] Health check passed (${i}s)"
    break
  fi
  if (( i == 15 )); then
    echo "[PromptHub] Router health check FAILED after ${i}s, killing PID $ROUTER_PID"
    kill "$ROUTER_PID" || true
    echo "[PromptHub] Check logs: tail -f $LOG_DIR/router-stderr.log"
    exit 1
  fi
  sleep 1
done

echo "[PromptHub] OpenAI-compatible API test (models)..."
curl -s "http://127.0.0.1:9090/v1/models" \
  -H "Authorization: Bearer sk-prompthub-claude-code-001" \
  | head -c 400 || true

echo "\n[PromptHub] Router is up (PID $ROUTER_PID). Tail logs with:"
echo "  tail -f \"$LOG_DIR/router-stderr.log\""

wait "$ROUTER_PID"
