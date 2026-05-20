#!/usr/bin/env bash
set -euo pipefail

# Installs the repo-tracked Qwen Code settings.json into Qwen Code's primary
# (~/.qwen) and compatibility (~/.config/qwen-code) locations.
#
# Uses **copy** rather than symlink because Qwen Code persists state in-place
# (e.g. on `/model` switch, `/auth`, etc.) — a symlink would let those writes
# clobber the repo-tracked source. With copy semantics, the live file is free
# to drift; re-running this script reinstalls the canonical version (after
# backing up the prior live file to <target>.bak-<timestamp>).
#
# To pull live edits back into the repo:
#   cp ~/.qwen/settings.json clients/qwen-code/settings.json
# (review with `git diff` before committing.)

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

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
for target in "${PRIMARY_TARGET_FILE}" "${COMPAT_TARGET_FILE}"; do
  if [ -L "${target}" ]; then
    rm -f "${target}"
    echo "Removed legacy symlink: ${target}"
  elif [ -f "${target}" ]; then
    backup="${target}.bak-${TIMESTAMP}"
    cp "${target}" "${backup}"
    echo "Backed up: ${target} -> ${backup}"
  fi
  cp "${SOURCE_FILE}" "${target}"
  echo "Installed: ${SOURCE_FILE} -> ${target}"
done

echo
echo "Done. Verify with: bash ${CLIENT_DIR}/check.sh"
echo
echo "Note: Qwen Code may rewrite ${PRIMARY_TARGET_FILE} on /model switch."
echo "Re-run this script to restore the canonical version (auto-backs-up first)."
