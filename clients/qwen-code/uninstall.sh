#!/usr/bin/env bash
set -euo pipefail

CANONICAL_FILE="${HOME}/.local/share/prompthub/clients/qwen-code/settings.json"
PRIMARY_TARGET_FILE="${HOME}/.qwen/settings.json"
COMPAT_TARGET_FILE="${HOME}/.config/qwen-code/settings.json"

for target in "${CANONICAL_FILE}" "${PRIMARY_TARGET_FILE}" "${COMPAT_TARGET_FILE}"; do
  if [ -L "${target}" ] || [ -e "${target}" ]; then
    rm -f "${target}"
    echo "Removed ${target}"
  else
    echo "No live Qwen Code config found at ${target}"
  fi
done
