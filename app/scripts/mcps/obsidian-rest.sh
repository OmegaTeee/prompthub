#!/bin/bash
# MCP Obsidian (Python-based) wrapper - loads API key from Keychain

OBSIDIAN_API_KEY="$(security find-generic-password -a "${USER}" -s "obsidian_api_key" -w 2>/dev/null)"
export OBSIDIAN_API_KEY
if [[ -z "${OBSIDIAN_API_KEY}" ]]; then
    echo "Error: OBSIDIAN_API_KEY not found in Keychain" >&2
    echo "Add it with: security add-generic-password -a \$USER -s obsidian_api_key -w YOUR_KEY" >&2
    exit 1
fi

OBSIDIAN_HOST="https://127.0.0.1"
export OBSIDIAN_HOST

OBSIDIAN_PORT="27124"
export OBSIDIAN_PORT

# Activate virtual environment and run mcp-obsidian
AGENTHUB_DIR="${HOME}/.local/share/agenthub"
source "${AGENTHUB_DIR}/.venv/bin/activate"
exec python -m mcp_obsidian "$@"
