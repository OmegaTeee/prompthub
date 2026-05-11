#!/usr/bin/env bash
set -euo pipefail

# Derive REPO_ROOT from this script's location so the hook is portable across
# checkouts (the previous hardcoded /Users/visualval/prompthub broke for anyone else).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# Drain Qwen Code's stop-hook JSON payload from stdin if one is piped in.
# Guarded by `[ ! -t 0 ]` so manual invocation (stdin is a TTY) doesn't hang
# waiting for input that will never arrive.
if [ ! -t 0 ]; then
  cat >/dev/null || true
fi

if "$REPO_ROOT/scripts/doc-drift/check-doc-drift.sh"; then
  printf '{"continue":true}\n'
else
  printf '{"continue":true,"decision":"block","reason":"Possible PromptHub doc drift detected. Update docs before finishing."}\n'
fi
