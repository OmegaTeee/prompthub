#!/bin/bash
# MCP Obsidian wrapper - loads API key from Keychain
# Keys are stored by Python keyring: service="prompthub", account=<key_name>

OBSIDIAN_API_KEY="$(security find-generic-password -s "prompthub" -a "obsidian_api_key" -w 2>/dev/null)"
export OBSIDIAN_API_KEY
if [[ -z "${OBSIDIAN_API_KEY}" ]]; then
    echo "Error: obsidian_api_key not found in Keychain (service=prompthub)" >&2
    echo "Store it with: python scripts/security/manage-keys.py set obsidian_api_key" >&2
    exit 1
fi

OBSIDIAN_HOST="https://127.0.0.1"
export OBSIDIAN_HOST

OBSIDIAN_PORT="27124"
export OBSIDIAN_PORT

exec "${HOME}/.local/bin/mcp-obsidian" "$@"
