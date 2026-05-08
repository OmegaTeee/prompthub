#!/usr/bin/env bash
set -euo pipefail

CLIENT_DIR="${HOME}/.local/share/prompthub/clients/qwen-code"
ACTIVE_FILE="${CLIENT_DIR}/settings.json"
DIRECT_FILE="${CLIENT_DIR}/settings.direct.json"
ROUTER_FILE="${CLIENT_DIR}/settings.router.json"
PRIMARY_TARGET="${HOME}/.qwen/settings.json"
COMPAT_TARGET="${HOME}/.config/qwen-code/settings.json"

resolve_link() {
  local path="$1"
  if [ -L "$path" ]; then
    readlink "$path"
  elif [ -e "$path" ]; then
    printf '%s\n' "(regular file)"
  else
    printf '%s\n' "(missing)"
  fi
}

mask_status() {
  local value="${1:-}"
  if [ -n "$value" ]; then
    printf 'present (%s chars)\n' "${#value}"
  else
    printf 'missing\n'
  fi
}

ACTIVE_TARGET="$(resolve_link "${ACTIVE_FILE}")"
PRIMARY_TARGET_VALUE="$(resolve_link "${PRIMARY_TARGET}")"
COMPAT_TARGET_VALUE="$(resolve_link "${COMPAT_TARGET}")"

case "${ACTIVE_TARGET}" in
  "${DIRECT_FILE}") MODE="direct" ;;
  "${ROUTER_FILE}") MODE="router" ;;
  *) MODE="unknown" ;;
esac

MODEL_NAME="$(
  python3 - <<'PY'
import json
from pathlib import Path
path = Path.home() / ".local/share/prompthub/clients/qwen-code/settings.json"
data = json.loads(path.read_text())
print(data["model"]["name"])
PY
)"

readarray -t CONFIG_FIELDS < <(
  python3 - <<'PY'
import json
from pathlib import Path
path = Path.home() / ".local/share/prompthub/clients/qwen-code/settings.json"
data = json.loads(path.read_text())
provider = data["modelProviders"]["openai"][0]
print(provider["baseUrl"])
print(provider["envKey"])
PY
)

BASE_URL="${CONFIG_FIELDS[0]}"
ENV_KEY="${CONFIG_FIELDS[1]}"
ENV_VALUE="$(printenv "${ENV_KEY}" || true)"

printf 'Qwen Code check\n'
printf 'Mode: %s\n' "${MODE}"
printf 'Active config: %s -> %s\n' "${ACTIVE_FILE}" "${ACTIVE_TARGET}"
printf 'Live config: %s -> %s\n' "${PRIMARY_TARGET}" "${PRIMARY_TARGET_VALUE}"
printf 'Compat config: %s -> %s\n' "${COMPAT_TARGET}" "${COMPAT_TARGET_VALUE}"
printf 'Model: %s\n' "${MODEL_NAME}"
printf 'Base URL: %s\n' "${BASE_URL}"
printf 'Env key: %s\n' "${ENV_KEY}"
printf 'Env value: %s' "$(mask_status "${ENV_VALUE}")"
