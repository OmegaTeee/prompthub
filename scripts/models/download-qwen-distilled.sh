#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/models/download-qwen-distilled.sh [--config PATH] [--out DIR] [--profile NAME] [--dry-run]

Downloads the "coder-first" distilled model set from Hugging Face using
`huggingface-cli download`, with a config file to make model swaps easy at
deployment time.

Profiles:
  claude_feel   Download the "Claude-feel" planning model
  coder         Download the primary coding+tools worker model
  daemon        Download the always-on router daemon model
  all           Download all profiles (default)

Auth:
  Prefers HF_TOKEN; also accepts HUGGINGFACE_API_KEY.

Examples:
  # Dry-run with defaults
  ./scripts/models/download-qwen-distilled.sh --dry-run

  # Download only the daemon profile to a custom directory
  HF_TOKEN=... ./scripts/models/download-qwen-distilled.sh --profile daemon --out ~/.prompthub/models

  # Use a deployment config file to swap repos/patterns without editing the script
  ./scripts/models/download-qwen-distilled.sh --config ./scripts/models/qwen-distilled.env.example
USAGE
}

CONFIG_PATH=""
OUT_DIR=""
PROFILE="all"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG_PATH="${2:-}"; shift 2 ;;
    --out) OUT_DIR="${2:-}"; shift 2 ;;
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN="true"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -n "$CONFIG_PATH" ]]; then
  if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "Config file not found: $CONFIG_PATH" >&2
    exit 2
  fi
  # shellcheck disable=SC1090
  source "$CONFIG_PATH"
fi

PH_MODELS_OUT_DIR_DEFAULT="${PH_MODELS_OUT_DIR:-$HOME/.prompthub/models}"
PH_MODELS_OUT_DIR="${OUT_DIR:-$PH_MODELS_OUT_DIR_DEFAULT}"

HF_TOKEN_EFFECTIVE="${PH_HF_TOKEN:-${HF_TOKEN:-${HUGGINGFACE_API_KEY:-}}}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing dependency: $1" >&2
    echo "Install: pipx install huggingface-hub  (or: pip install -U huggingface-hub)" >&2
    exit 2
  fi
}

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

  local -a cmd=(huggingface-cli download "$repo" --local-dir "$dest" --local-dir-use-symlinks False --include "$include_glob")
  # Never echo tokens in --dry-run output; only pass tokens for real downloads.
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

# Defaults live here, but are intended to be overridden by --config at deploy time.
PH_MODEL_CLAUDE_FEEL_REPO="${PH_MODEL_CLAUDE_FEEL_REPO:-JackRong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF}"
PH_MODEL_CLAUDE_FEEL_GLOB="${PH_MODEL_CLAUDE_FEEL_GLOB:-*.gguf}"

PH_MODEL_CODER_REPO="${PH_MODEL_CODER_REPO:-JackRong/Qwopus3.5-9B-Coder-GGUF}"
PH_MODEL_CODER_GLOB="${PH_MODEL_CODER_GLOB:-*.gguf}"

PH_MODEL_DAEMON_REPO="${PH_MODEL_DAEMON_REPO:-JackRong/Qwopus3.5-4B-v3-GGUF}"
PH_MODEL_DAEMON_GLOB="${PH_MODEL_DAEMON_GLOB:-*.gguf}"

if [[ -z "$HF_TOKEN_EFFECTIVE" && "$DRY_RUN" != "true" ]]; then
  echo "[models] Note: no HF token provided (HF_TOKEN/HUGGINGFACE_API_KEY). Public repos will work; gated/private repos will fail." >&2
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

echo "[models] Done. Import the downloaded GGUF files into LM Studio, then ensure PromptHub is pointed at the intended model IDs."
