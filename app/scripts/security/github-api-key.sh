#!/bin/bash
# GitHub API Key wrapper - loads API key from Keychain

GITHUB_API_KEY="$(security find-generic-password -a "${USER}" -s "github_api_key" -w 2>/dev/null)"
export GITHUB_API_KEY
if [[ -z "${GITHUB_API_KEY}" ]]; then
    echo "Error: GITHUB_API_KEY not found in Keychain" >&2
    echo "Add it with: security add-generic-password -a \$USER -s github_api_key -w YOUR_KEY" >&2
    exit 1
fi

# exec node /path/to/github-api-key/dist/index.js "$@"