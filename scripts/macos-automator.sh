#!/usr/bin/env bash
# Send a prompt to the local PromptHub router and print the reply.
# Usage: macos-automator.sh "your prompt"
set -euo pipefail

# Token from env (sourced from Keychain via PH_API_TOKEN); falls back to the
# local default key. Never hard-code real credentials in tracked files.
API_KEY="${PH_API_TOKEN:-sk-prompthub-default-001}"
PROMPT="${1:?usage: macos-automator.sh \"your prompt\"}"

# JSON-encode the prompt so quotes/newlines can't break or inject into the body.
# Use 127.0.0.1 (not localhost) — macOS resolves localhost to IPv6 first, which
# fails if the router only binds IPv4.
BODY=$(PROMPT="$PROMPT" python3 -c '
import json, os
print(json.dumps({
    "model": "qwen3-4b-instruct-2507",
    "messages": [{"role": "user", "content": os.environ["PROMPT"]}],
}))')

curl -s http://127.0.0.1:9090/v1/chat/completions \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$BODY" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
