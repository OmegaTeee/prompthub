#!/usr/bin/env bash
set -euo pipefail

# Symlinks the repo-tracked Qwen Code settings.json into both the primary
# (~/.qwen) and compatibility (~/.config/qwen-code) locations so Qwen Code
# reads the in-repo source of truth regardless of which path it inspects.
#
# Single unified settings.json (no per-provider modes). Provider selection
# happens at runtime via Qwen Code's /model picker — PromptHub Router is
# the default; Direct LM Studio and OpenRouter Free are listed as alternates.

CLIENT_DIR="${HOME}/.local/share/prompthub/clients/qwen-code"
SOURCE_FILE="${CLIENT_DIR}/settings.json"
PRIMARY_TARGET_DIR="${HOME}/.qwen"
PRIMARY_TARGET_FILE="${PRIMARY_TARGET_DIR}/settings.json"
COMPAT_TARGET_DIR="${HOME}/.config/qwen-code"
COMPAT_TARGET_FILE="${COMPAT_TARGET_DIR}/settings.json"

if [ ! -f "${SOURCE_FILE}" ]; then
  echo "Source not found: ${SOURCE_FILE}" >&2
  exit 1
fi

mkdir -p "${PRIMARY_TARGET_DIR}" "${COMPAT_TARGET_DIR}"

for target in "${PRIMARY_TARGET_FILE}" "${COMPAT_TARGET_FILE}"; do
  if [ -e "${target}" ] || [ -L "${target}" ]; then
    rm -f "${target}"
  fi
  ln -s "${SOURCE_FILE}" "${target}"
  echo "Linked ${target} -> ${SOURCE_FILE}"
done

echo
echo "Done. Verify with: bash ${CLIENT_DIR}/check.sh"
