#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Files that satisfy the drift gate when changed.
DOC_PATTERNS='^(README\.md|QUICKSTART\.md|AGENTS\.md|CHANGELOG\.md|docs/|clients/.*/README\.md|clients/README\.md|clients/WORKFLOW\.md|clients/TOOL_USE\.md|scripts/README\.md|app/README\.md|app/AGENTS\.md)'
# Files that trigger the drift gate when changed without an accompanying doc update.
# Note: README.md/QUICKSTART.md/AGENTS.md appear in both — editing them satisfies their own gate.
CODE_PATTERNS='^(app/|clients/|mcps/|scripts/|\.github/workflows/|\.mcp\.json|llm\.txt|README\.md|QUICKSTART\.md|AGENTS\.md)'
# Always-exempt paths: archives, runtime logs, tests, the drift system itself.
IGNORE_PATTERNS='^(docs/archive/|logs/|.*\.DS_Store$|app/tests/|.*/tests/|.*/test_[^/]+\.py$|scripts/doc-drift/)'

# Hard escape hatch: env var, always works. Use for one-off bypass:
#   DOC_DRIFT_SKIP=1 git commit -m "..."
if [[ "${DOC_DRIFT_SKIP:-}" == "1" ]]; then
  exit 0
fi

if git diff --cached --quiet --exit-code && [[ "$MODE" == "--staged" ]]; then
  exit 0
fi

if [[ "$MODE" == "--staged" ]]; then
  CHANGED_FILES="$(git diff --cached --name-only --diff-filter=ACMR)"
elif [[ -n "${DOC_DRIFT_BASE_SHA:-}" ]]; then
  # Workflow may pass an explicit base SHA (e.g. github.event.before for push events
  # where GITHUB_BASE_REF is unset). Prefer it when set.
  BASE_REF="$DOC_DRIFT_BASE_SHA"
  if ! git rev-parse --verify --quiet "$BASE_REF^{commit}" >/dev/null; then
    echo "❌ doc-drift: DOC_DRIFT_BASE_SHA='$BASE_REF' is not a valid commit." >&2
    exit 1
  fi
  CHANGED_FILES="$(git diff --name-only --diff-filter=ACMR "$BASE_REF"...HEAD)"
else
  # In GH Actions GITHUB_BASE_REF is the branch name (e.g. "main"); prefix with origin/
  # to reference the remote-tracking ref that actions/checkout fetch-depth: 0 supplies.
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    BASE_REF="origin/${GITHUB_BASE_REF}"
  else
    BASE_REF="origin/main"
  fi
  if ! git rev-parse --verify --quiet "$BASE_REF" >/dev/null; then
    echo "❌ doc-drift: BASE_REF '$BASE_REF' does not exist." >&2
    echo "   Run 'git fetch origin' or set DOC_DRIFT_BASE_SHA to an explicit commit." >&2
    exit 1
  fi
  CHANGED_FILES="$(git diff --name-only --diff-filter=ACMR "$BASE_REF"...HEAD)"
fi

CHANGED_FILES="$(printf '%s\n' "$CHANGED_FILES" | sed '/^$/d' | grep -Ev "$IGNORE_PATTERNS" || true)"

if [[ -z "$CHANGED_FILES" ]]; then
  exit 0
fi

# Soft escape hatch: [doc-drift:ignore] in the most recent commit message.
# Only honored in CI mode — in pre-commit mode the new commit doesn't exist yet,
# so this would check the *previous* commit's message. Use DOC_DRIFT_SKIP=1 instead.
if [[ "$MODE" != "--staged" ]] && git log -1 --pretty=%B 2>/dev/null | grep -qi '\[doc-drift:ignore\]'; then
  exit 0
fi

CODE_CHANGED="$(printf '%s\n' "$CHANGED_FILES" | grep -E "$CODE_PATTERNS" || true)"
DOC_CHANGED="$(printf '%s\n' "$CHANGED_FILES" | grep -E "$DOC_PATTERNS" || true)"

if [[ -z "$CODE_CHANGED" ]]; then
  exit 0
fi

if [[ -z "$DOC_CHANGED" ]]; then
  echo "❌ Possible documentation drift detected."
  echo
  echo "Code/config/runtime files changed:"
  while IFS= read -r file; do
    [[ -n "$file" ]] && printf '  - %s\n' "$file"
  done <<< "$CODE_CHANGED"
  echo
  echo "But no tracked docs changed. Update one or more of:"
  echo "  - README.md"
  echo "  - QUICKSTART.md"
  echo "  - AGENTS.md"
  echo "  - docs/**"
  echo "  - clients/README.md, clients/WORKFLOW.md, clients/TOOL_USE.md"
  echo "  - scripts/README.md"
  echo "  - app/README.md, app/AGENTS.md"
  echo
  echo "If this change truly needs no docs update, either:"
  echo "  - Run with DOC_DRIFT_SKIP=1 (works for both pre-commit and CI), or"
  echo "  - Add [doc-drift:ignore] to the commit message (CI only), or"
  echo "  - git commit --no-verify"
  exit 1
fi

LM_URL="${DOC_DRIFT_LMSTUDIO_URL:-http://127.0.0.1:1234}"
LM_MODEL="${DOC_DRIFT_MODEL:-qwen3-4b-instruct-2507}"

if command -v python3 >/dev/null 2>&1 && command -v curl >/dev/null 2>&1; then
  PROMPT_JSON="$(CHANGED_FILES_FOR_PROMPT="$CHANGED_FILES" python3 - <<'PY'
import json, os
changed = os.environ.get('CHANGED_FILES_FOR_PROMPT', '')
msg = (
    'Changed files in PromptHub:\n' + changed +
    '\n\nReturn strict JSON only: '
    '{"result":"pass|warn|fail","reason":"...","docs_to_update":["..."]}. '
    'Mark fail only if docs are likely stale. Mark warn if uncertain.'
)
print(json.dumps(msg))
PY
)"

  PAYLOAD=$(cat <<EOF
{"model":"$LM_MODEL","messages":[{"role":"system","content":"You review repository doc drift for PromptHub. Output strict JSON only."},{"role":"user","content":$PROMPT_JSON}],"temperature":0.1}
EOF
)

  # --max-time caps the total request to keep slow/wedged LM Studio from blocking commits.
  LLM_RESPONSE="$(curl -fsS --max-time 15 "$LM_URL/v1/chat/completions" -H 'Content-Type: application/json' -d "$PAYLOAD" 2>/dev/null || true)"
  if [[ -n "$LLM_RESPONSE" ]] && printf '%s' "$LLM_RESPONSE" | grep -q '"fail"'; then
    echo
    echo "⚠️ LM Studio review (${LM_MODEL}) suggests docs are likely stale."
    echo "$LLM_RESPONSE"
    exit 1
  fi
fi

exit 0
