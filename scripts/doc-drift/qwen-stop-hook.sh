#!/usr/bin/env bash
set -euo pipefail

# Derive REPO_ROOT from this script's location so the hook is portable across
# checkouts (the previous hardcoded /Users/visualval/prompthub broke for anyone else).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# Drain Qwen Code's stop-hook JSON payload from stdin so the pipe doesn't break.
# We don't currently use it, but reading it prevents a SIGPIPE if Qwen sends a large message.
cat >/dev/null || true

if "$REPO_ROOT/scripts/doc-drift/check-doc-drift.sh"; then
  printf '{"continue":true}\n'
else
  printf '{"continue":true,"decision":"block","reason":"Possible PromptHub doc drift detected. Update docs before finishing."}\n'
fi
