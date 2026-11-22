#!/usr/bin/env zsh
# Make sure LM Studio's server is up and the router's model is loaded under the
# identifier the configs use (LLM_MODEL / model_profiles). Safe to re-run: does
# nothing if the model is already loaded. Run at login by com.prompthub.lms.
#
# Environment overrides:
#   LMS_BIN             lms CLI (default ~/.lmstudio/bin/lms)
#   LMS_MODEL_KEY       model to load (default the qwen3.5 4B distill)
#   LMS_IDENTIFIER      API identifier (default qwen3.5-4b-distill)
#   LMS_CONTEXT_LENGTH  default 8192
#   LMS_PARALLEL        default 2
#   LMS_GPU             offload ratio, "off" or "max" (default 0.5)
#   LMS_WAIT            seconds to wait for LM Studio to come up (default 120)

set -euo pipefail

LMS="${LMS_BIN:-$HOME/.lmstudio/bin/lms}"
MODEL_KEY="${LMS_MODEL_KEY:-qwen3.5-4b-emperoai-qwen3.8-distill-heretic-abliterated}"
IDENTIFIER="${LMS_IDENTIFIER:-qwen3.5-4b-distill}"
CONTEXT_LENGTH="${LMS_CONTEXT_LENGTH:-8192}"
PARALLEL="${LMS_PARALLEL:-2}"
GPU="${LMS_GPU:-0.5}"
WAIT="${LMS_WAIT:-120}"

say() { print -r -- "[lms-start] $(date '+%F %T') $*"; }
die() { print -r -- "[lms-start] $(date '+%F %T') ERROR: $*" >&2; exit 1; }

[[ -x "$LMS" ]] || die "lms CLI not found at $LMS"

# At login LM Studio may still be starting; retry until the server answers.
started=0
for (( i = 0; i < WAIT; i += 5 )); do
  if "$LMS" server start > /dev/null 2>&1; then started=1; break; fi
  sleep 5
done
(( started )) || die "LM Studio server did not start within ${WAIT}s"
say "LM Studio server is running."

loaded() {
  "$LMS" ps --json | /usr/bin/python3 -c '
import json, sys
sys.exit(0 if any(m.get("identifier") == sys.argv[1] for m in json.load(sys.stdin)) else 1)
' "$IDENTIFIER"
}

if loaded; then
  say "Model '$IDENTIFIER' already loaded; nothing to do."
  exit 0
fi

say "Loading $MODEL_KEY as '$IDENTIFIER' (ctx $CONTEXT_LENGTH, parallel $PARALLEL, gpu $GPU)..."
"$LMS" load "$MODEL_KEY" --yes \
  --identifier "$IDENTIFIER" \
  --context-length "$CONTEXT_LENGTH" \
  --parallel "$PARALLEL" \
  --gpu "$GPU" 2>&1 | tail -n 3   # drop the progress spinner; pipefail keeps the exit code
loaded || die "lms load returned but '$IDENTIFIER' is not in 'lms ps'"
say "Model '$IDENTIFIER' loaded."
