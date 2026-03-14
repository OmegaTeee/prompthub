#!/bin/bash
# stop.sh — Stop Open WebUI
#
# Usage:
#   ./stop.sh              # Stop on default port 3000
#   OWUI_PORT=8080 ./stop.sh  # Stop on custom port

set -euo pipefail

OWUI_PORT="${OWUI_PORT:-3000}"

echo "Stopping Open WebUI on port $OWUI_PORT..."

# Find and kill process listening on the port
PID=$(lsof -ti :"$OWUI_PORT" -sTCP:LISTEN 2>/dev/null || true)

if [[ -z "$PID" ]]; then
    echo "No process found on port $OWUI_PORT"
    exit 0
fi

echo "  Killing PID $PID"
kill "$PID" 2>/dev/null || true

# Wait briefly for graceful shutdown
sleep 2

# Force kill if still running
if kill -0 "$PID" 2>/dev/null; then
    echo "  Force killing PID $PID"
    kill -9 "$PID" 2>/dev/null || true
fi

echo "Open WebUI stopped."
