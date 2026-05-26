#!/usr/bin/env bash
# =============================================================================
# Download the "coder-first" distilled Qwen model set from Hugging Face.
#
# Wraps `huggingface-cli download` with a small profile system so the same
# script handles every model the router can opt into via `model_profile`
# (see app/configs/enhancement-rules.json). Repos and glob patterns are
# env-var driven and can be overridden via --config — that file is the
# single swap point when models change at deployment time.
#
# Output layout:
#   $PH_MODELS_OUT_DIR/
#     claude_feel/   <- gguf shards for the "Claude-feel" planner
#     coder/         <- gguf shards for the primary coding worker
#     daemon/        <- gguf shards for the router daemon model
# =============================================================================
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/models/download-qwen-distilled.sh [--config PATH] [--out DIR] [--profile NAME] [--dry-run]

Profiles (matching enhancement-rules.json model_profiles):
  daemon        Router daemon / always-on model
  coder         Primary coding + tools worker
  claude_feel   "Claude-feel" planning model
  all           Download every profile (default)

Options:
  --config PATH    .env-style file overriding the repo/glob env vars
  --out DIR        Output root directory (default: $PH_MODELS_OUT_DIR
                   or ~/.prompthub/models if unset)
  --profile NAME   One of daemon|coder|claude_feel|all (default: all)
  --dry-run        Print the huggingface-cli invocations without running them.
                   Never passes --token in this mode.
  -h, --help       Show this help and exit.

Auth:
  Prefers PH_HF_TOKEN; falls back to HF_TOKEN; finally HUGGINGFACE_API_KEY.
  Public repos work with no token; gated/private repos require one.

Examples:
  # Dry-run the full set with defaults
  ./scripts/models/download-qwen-distilled.sh --dry-run

  # Download only the daemon profile to a custom directory
  HF_TOKEN=hf_… ./scripts/models/download-qwen-distilled.sh \
      --profile daemon --out ~/.prompthub/models

  # Use a deployment config to swap the repo without editing the script
  ./scripts/models/download-qwen-distilled.sh \
      --config ./scripts/models/qwen-distilled.env.example
USAGE
}

CONFIG_PATH=""
OUT_DIR=""
PROFILE="all"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)  CONFIG_PATH="${2:-}"; shift 2 ;;
    --out)     OUT_DIR="${2:-}"; shift 2 ;;
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN="true"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

# Load --config first so it can override the defaults below. The file is
# sourced into the current shell; treat it like deploy-time config, not
# untrusted input.
if [[ -n "$CONFIG_PATH" ]]; then
  if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "Config file not found: $CONFIG_PATH" >&2
    exit 2
  fi
  # shellcheck disable=SC1090
  source "$CONFIG_PATH"
fi

# Output directory: --out > $PH_MODELS_OUT_DIR > ~/.prompthub/models.
PH_MODELS_OUT_DIR_DEFAULT="${PH_MODELS_OUT_DIR:-$HOME/.prompthub/models}"
PH_MODELS_OUT_DIR="${OUT_DIR:-$PH_MODELS_OUT_DIR_DEFAULT}"

# Token resolution: PH_HF_TOKEN > HF_TOKEN > HUGGINGFACE_API_KEY.
# Empty string means "no token" (anonymous downloads).
HF_TOKEN_EFFECTIVE="${PH_HF_TOKEN:-${HF_TOKEN:-${HUGGINGFACE_API_KEY:-}}}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing dependency: $1" >&2
    echo "Install: pipx install huggingface-hub  (or: pip install -U huggingface-hub)" >&2
    exit 2
  fi
}

# Run a command or print it under dry-run. Never echo tokens.
run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    printf '[dry-run] %q' "$1"
    shift
    for a in "$@"; do printf ' %q' "$a"; done
    printf '\n'
    return 0
  fi
  "$@"
}

download_repo() {
  local profile_name="$1"
  local repo="$2"
  local include_glob="$3"
  local dest="$4"

  if [[ -z "$repo" || -z "$include_glob" ]]; then
    echo "Missing config for profile '$profile_name' (repo/include glob)." >&2
    exit 2
  fi

  if [[ "$DRY_RUN" != "true" ]]; then
    mkdir -p "$dest"
  fi

  # --local-dir-use-symlinks False keeps the downloaded shards in $dest
  # rather than symlinking from the global HF cache. Critical for LM
  # Studio's import flow and prevents cache-poisoning via symlinks.
  local -a cmd=(
    huggingface-cli download "$repo"
    --local-dir "$dest"
    --local-dir-use-symlinks False
    --include "$include_glob"
  )
  # Only pass the token for real downloads. Dry-run never echoes it.
  if [[ -n "$HF_TOKEN_EFFECTIVE" && "$DRY_RUN" != "true" ]]; then
    cmd+=(--token "$HF_TOKEN_EFFECTIVE")
  fi

  echo "[models] $profile_name: $repo ($include_glob) -> $dest"
  if [[ -n "$HF_TOKEN_EFFECTIVE" && "$DRY_RUN" == "true" ]]; then
    echo "[models] (dry-run) HF token detected (redacted)."
  fi
  run "${cmd[@]}"
}

require_cmd huggingface-cli

case "$PROFILE" in
  claude_feel|coder|daemon|all) ;;
  *) echo "Invalid --profile: $PROFILE" >&2; usage; exit 2 ;;
esac

# Defaults live here, but are intended to be overridden by --config at
# deploy time. Treat this list as the "vendor-default coder-first set."
PH_MODEL_CLAUDE_FEEL_REPO="${PH_MODEL_CLAUDE_FEEL_REPO:-JackRong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF}"
PH_MODEL_CLAUDE_FEEL_GLOB="${PH_MODEL_CLAUDE_FEEL_GLOB:-*.gguf}"

PH_MODEL_CODER_REPO="${PH_MODEL_CODER_REPO:-JackRong/Qwopus3.5-9B-Coder-GGUF}"
PH_MODEL_CODER_GLOB="${PH_MODEL_CODER_GLOB:-*.gguf}"

PH_MODEL_DAEMON_REPO="${PH_MODEL_DAEMON_REPO:-JackRong/Qwopus3.5-4B-v3-GGUF}"
PH_MODEL_DAEMON_GLOB="${PH_MODEL_DAEMON_GLOB:-*.gguf}"

if [[ -z "$HF_TOKEN_EFFECTIVE" && "$DRY_RUN" != "true" ]]; then
  echo "[models] Note: no HF token provided (PH_HF_TOKEN/HF_TOKEN/HUGGINGFACE_API_KEY)." >&2
  echo "[models]       Public repos will work; gated/private repos will fail." >&2
fi

if [[ "$PROFILE" == "claude_feel" || "$PROFILE" == "all" ]]; then
  download_repo "claude_feel" "$PH_MODEL_CLAUDE_FEEL_REPO" "$PH_MODEL_CLAUDE_FEEL_GLOB" "$PH_MODELS_OUT_DIR/claude_feel"
fi
if [[ "$PROFILE" == "coder" || "$PROFILE" == "all" ]]; then
  download_repo "coder" "$PH_MODEL_CODER_REPO" "$PH_MODEL_CODER_GLOB" "$PH_MODELS_OUT_DIR/coder"
fi
if [[ "$PROFILE" == "daemon" || "$PROFILE" == "all" ]]; then
  download_repo "daemon" "$PH_MODEL_DAEMON_REPO" "$PH_MODEL_DAEMON_GLOB" "$PH_MODELS_OUT_DIR/daemon"
fi

echo "[models] Done. Import the downloaded GGUF files into LM Studio, then"
echo "[models] ensure PromptHub is pointed at the intended model IDs (see"
echo "[models] app/configs/enhancement-rules.json -> model_profiles)."
