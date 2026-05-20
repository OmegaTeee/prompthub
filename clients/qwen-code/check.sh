#!/usr/bin/env bash
set -euo pipefail

# Reports the current Qwen Code config state: symlink targets, default model,
# fastModel, and whether the env vars referenced by each provider are set.
# No mode logic — single unified settings.json since the toggle pattern was
# retired. Provider switching happens at runtime via Qwen Code's /model picker.

CLIENT_DIR="${HOME}/.local/share/prompthub/clients/qwen-code"
SOURCE_FILE="${CLIENT_DIR}/settings.json"
PRIMARY_TARGET="${HOME}/.qwen/settings.json"
COMPAT_TARGET="${HOME}/.config/qwen-code/settings.json"

# setup.sh installs as a copy (not symlink) so Qwen Code's in-place persistence
# (on /model, /auth, etc.) doesn't clobber the repo-tracked source. So a regular
# file at the target IS the expected state. We compare its content to the repo
# source to surface drift.
describe_target() {
  local path="$1"
  local source="$2"
  if [ -L "$path" ]; then
    printf 'symlink → %s (legacy install; re-run setup.sh)' "$(readlink "$path")"
  elif [ -f "$path" ]; then
    if cmp -s "$path" "$source"; then
      printf 'in sync with repo'
    else
      printf 'DRIFTED from repo (Qwen Code likely rewrote it; re-run setup.sh to reset)'
    fi
  else
    printf 'missing (run setup.sh)'
  fi
}

mask_status() {
  local value="${1:-}"
  if [ -n "$value" ]; then
    printf 'present (%s chars)' "${#value}"
  else
    printf 'missing'
  fi
}

PRIMARY_TARGET_VALUE="$(describe_target "${PRIMARY_TARGET}" "${SOURCE_FILE}")"
COMPAT_TARGET_VALUE="$(describe_target "${COMPAT_TARGET}" "${SOURCE_FILE}")"

# Pull default model, fastModel, and unique providers from settings.json.
read -r DEFAULT_MODEL FAST_MODEL <<< "$(
  python3 - <<'PY'
import json
from pathlib import Path
data = json.loads((Path.home() / ".local/share/prompthub/clients/qwen-code/settings.json").read_text())
print(data["model"]["name"], data.get("fastModel", "(unset)"))
PY
)"

printf 'Qwen Code config check\n'
printf '  Source:       %s\n' "${SOURCE_FILE}"
printf '  ~/.qwen:      %s\n' "${PRIMARY_TARGET_VALUE}"
printf '  ~/.config:    %s\n' "${COMPAT_TARGET_VALUE}"
printf '  Default model: %s\n' "${DEFAULT_MODEL}"
printf '  fastModel:     %s\n' "${FAST_MODEL}"
printf '\n'
printf 'Env vars referenced by providers:\n'
printf '  LM_API_TOKEN:        %s\n' "$(mask_status "${LM_API_TOKEN:-}")"
printf '  PROMPTHUB_API_KEY:   %s\n' "$(mask_status "${PROMPTHUB_API_KEY:-}")"
printf '  OPENROUTER_API_KEY:  %s\n' "$(mask_status "${OPENROUTER_API_KEY:-}")"
printf '\n'
printf 'Providers (id @ baseUrl) in /model picker order:\n'
# Qwen Code does not interpolate ${VAR} in baseUrl strings — they're passed
# to fetch() literally. So baseUrls in settings.json are stored as fully
# resolved URLs, and we display them as-is here.
python3 - <<'PY'
import json
from pathlib import Path

data = json.loads((Path.home() / ".local/share/prompthub/clients/qwen-code/settings.json").read_text())
for p in data["modelProviders"]["openai"]:
    print(f'  - {p["id"]:35s} @ {p["baseUrl"]}')
    print(f'    {p["name"]}')
PY
