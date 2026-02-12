#!/bin/bash
#
# MCP stdio Bridge for Claude Desktop
#
# This script bridges Claude Desktop's stdio transport to PromptHub's HTTP API.
# It stays running and forwards JSON-RPC requests bidirectionally.
#
# Usage:
#   mcp-stdio-bridge.sh <server-name> [prompthub-url]
#
# Arguments:
#   server-name: MCP server to connect to (e.g., "context7", "desktop-commander")
#   prompthub-url: Optional PromptHub URL (default: http://localhost:9090)
#

set -euo pipefail

SERVER_NAME="${1:-}"
PROMPTHUB_URL="${2:-http://localhost:9090}"

if [[ -z "${SERVER_NAME}" ]]; then
  echo "Error: SERVER_NAME required" >&2
  echo "Usage: $0 <server-name> [prompthub-url]" >&2
  exit 1
fi

# Log to stderr (stdout is for JSON-RPC responses)
log() {
  echo "[mcp-bridge] $*" >&2
}

log "Starting MCP stdio bridge for server: ${SERVER_NAME}"
log "PromptHub URL: ${PROMPTHUB_URL}"

# Read JSON-RPC from stdin line by line and forward to PromptHub
while IFS= read -r line; do
  # Skip empty lines
  if [[ -z "${line}" ]]; then
    continue
  fi

  log "Received request: ${line:0:100}..."

  # Forward to PromptHub via curl
  response=$(curl -s -X POST \
    "${PROMPTHUB_URL}/mcp/${SERVER_NAME}/tools/call" \
    -H "Content-Type: application/json" \
    -H "X-Client-Name: claude-desktop" \
    -d "${line}" 2>&1) || {
    # If curl fails, return JSON-RPC error
    log "ERROR: curl failed with exit code ${?}"
    echo '{"jsonrpc":"2.0","error":{"code":-32603,"message":"Internal error: PromptHub connection failed"},"id":null}'
    continue
  }

  log "Received response: ${response:0:100}..."

  # Transform FastAPI error responses to JSON-RPC format
  # Claude Desktop expects JSON-RPC 2.0, but PromptHub may return FastAPI errors with "detail" field
  if echo "${response}" | grep -q '"detail"'; then
    log "Detected FastAPI error response, transforming to JSON-RPC format"

    # Extract request ID from original request (default to null if not found)
    request_id=$(echo "${line}" | grep -o '"id":[^,}]*' | cut -d: -f2 | tr -d ' ' || echo "null")

    # Extract error detail message
    error_msg=$(echo "${response}" | grep -o '"detail":"[^"]*"' | cut -d'"' -f4)

    # Construct proper JSON-RPC error response
    response="{\"jsonrpc\":\"2.0\",\"error\":{\"code\":-32001,\"message\":\"${error_msg}\"},\"id\":${request_id}}"
    log "Transformed response: ${response}"
  fi

  # Send response to stdout (back to Claude Desktop)
  echo "${response}"
done

log "Bridge terminated"
