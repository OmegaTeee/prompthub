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
# Reads the env block from settings.json and substitutes ${VAR} placeholders in
# baseUrl values, so this stays accurate when the env block changes.
python3 - <<'PY'
import json, re
from pathlib import Path

data = json.loads((Path.home() / ".local/share/prompthub/clients/qwen-code/settings.json").read_text())
env_block = data.get("env", {})


def expand(value: str) -> str:
    # ${VAR} placeholders resolve against the settings.json env block.
    # Unresolved placeholders pass through unchanged so the user sees them.
    return re.sub(r"\$\{(\w+)\}", lambda m: env_block.get(m.group(1), m.group(0)), value)


for p in data["modelProviders"]["openai"]:
    print(f'  - {p["id"]:35s} @ {expand(p["baseUrl"])}')
    print(f'    {p["name"]}')
PY
