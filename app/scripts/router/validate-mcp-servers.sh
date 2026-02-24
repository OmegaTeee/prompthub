#!/usr/bin/env bash
# Validate MCP server binaries and dependencies exist on disk.
# Reads server commands from configs/mcp-servers.json dynamically.
set -euo pipefail

PROMPTHUB_DIR="${HOME}/.local/share/prompthub"
CONFIG="${PROMPTHUB_DIR}/app/configs/mcp-servers.json"

NODE=$(command -v node || true)
echo "node: ${NODE:-not-found}" && { [[ -n "${NODE:-}" ]] && ${NODE} --version || true; }
echo ""

if [[ ! -f "${CONFIG}" ]]; then
  echo "ERROR: Config not found: ${CONFIG}"
  exit 1
fi

echo "Checking configured server binaries..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PASS=0
FAIL=0

# Parse each server from mcp-servers.json
for name in $(python3 -c "import json; d=json.load(open('${CONFIG}')); print(' '.join(d['servers'].keys()))"); do
  command=$(python3 -c "
import json
d = json.load(open('${CONFIG}'))
s = d['servers']['${name}']
cmd = s['command']
args = s.get('args', [])
# For node commands, the binary to check is the first arg
if cmd == 'node' and args:
    # Resolve relative paths from workspace root
    arg = args[0]
    if arg.startswith('./'):
        print('${PROMPTHUB_DIR}/' + arg[2:])
    else:
        print(arg)
else:
    print(cmd)
")

  printf "  %-25s " "${name}:"
  if [[ -f "${command}" ]]; then
    echo "FOUND  ${command}"
    ((PASS++))
  elif command -v "${command}" &>/dev/null; then
    echo "FOUND  $(command -v "${command}")"
    ((PASS++))
  else
    echo "MISSING  ${command}"
    ((FAIL++))
  fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Result: ${PASS} found, ${FAIL} missing"

if [[ ${FAIL} -gt 0 ]]; then
  echo ""
  echo "Fix missing servers with: cd mcps && npm install"
  exit 1
fi
