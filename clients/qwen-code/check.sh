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

resolve_link() {
  local path="$1"
  if [ -L "$path" ]; then
    readlink "$path"
  elif [ -e "$path" ]; then
    printf '%s\n' "(regular file, not a symlink)"
  else
    printf '%s\n' "(missing)"
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

PRIMARY_TARGET_VALUE="$(resolve_link "${PRIMARY_TARGET}")"
COMPAT_TARGET_VALUE="$(resolve_link "${COMPAT_TARGET}")"

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
python3 - <<'PY'
import json, os
from pathlib import Path
data = json.loads((Path.home() / ".local/share/prompthub/clients/qwen-code/settings.json").read_text())
for p in data["modelProviders"]["openai"]:
    base = p["baseUrl"].replace("${LM_BASE_URL}", "http://127.0.0.1:1234/v1").replace("${PROMPTHUB_BASE_URL}", "http://127.0.0.1:9090/v1")
    print(f'  - {p["id"]:35s} @ {base}')
    print(f'    {p["name"]}')
PY
