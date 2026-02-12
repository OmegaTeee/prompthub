#!/bin/bash
# Obsidian MCP Tools wrapper - loads API key from Keychain

OBSIDIAN_API_KEY="$(security find-generic-password -a "${USER}" -s "obsidian_api_key" -w 2>/dev/null)"
export OBSIDIAN_API_KEY
if [[ -z "${OBSIDIAN_API_KEY}" ]]; then
    echo "Error: OBSIDIAN_API_KEY not found in Keychain" >&2
    echo "Add it with: security add-generic-password -a \$USER -s obsidian_api_key -w YOUR_KEY" >&2
    exit 1
fi

exec "${HOME}/.local/share/agenthub/mcps/obsidian-mcp-tools/bin/mcp-server" "$@"