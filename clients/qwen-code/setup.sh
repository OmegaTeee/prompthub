#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-direct}"
CLIENT_DIR="${HOME}/.local/share/prompthub/clients/qwen-code"
case "${MODE}" in
  direct)
    SOURCE_FILE="${CLIENT_DIR}/settings.direct.json"
    ;;
  router)
    SOURCE_FILE="${CLIENT_DIR}/settings.router.json"
    ;;
  *)
    echo "Usage: $0 [direct|router]" >&2
    exit 1
    ;;
esac

CANONICAL_FILE="${CLIENT_DIR}/settings.json"
PRIMARY_TARGET_DIR="${HOME}/.qwen"
PRIMARY_TARGET_FILE="${PRIMARY_TARGET_DIR}/settings.json"
COMPAT_TARGET_DIR="${HOME}/.config/qwen-code"
COMPAT_TARGET_FILE="${COMPAT_TARGET_DIR}/settings.json"

mkdir -p "${PRIMARY_TARGET_DIR}" "${COMPAT_TARGET_DIR}"

if [ -e "${CANONICAL_FILE}" ] || [ -L "${CANONICAL_FILE}" ]; then
  rm -f "${CANONICAL_FILE}"
fi
ln -s "${SOURCE_FILE}" "${CANONICAL_FILE}"
echo "Linked ${CANONICAL_FILE} -> ${SOURCE_FILE}"

for target in "${PRIMARY_TARGET_FILE}" "${COMPAT_TARGET_FILE}"; do
  if [ -e "${target}" ] || [ -L "${target}" ]; then
    rm -f "${target}"
  fi
  ln -s "${CANONICAL_FILE}" "${target}"
  echo "Linked ${target} -> ${CANONICAL_FILE}"
done
