#!/usr/bin/env bash
# Quick validation script for configured MCP servers
set -euo pipefail

NODE=$(command -v node || true)
NPX=$(command -v npx || true)

echo "node: ${NODE:-not-found}" && { [[ -n "${NODE:-}" ]] && ${NODE} --version || true; }
echo "npx: ${NPX:-not-found}" && { [[ -n "${NPX:-}" ]] && ${NPX} --version || true; }

echo "Checking configured server files/commands..."

PROMPTHUB_DIR="${HOME}/.local/share/prompthub"

FILES=(
  "${PROMPTHUB_DIR}/mcps/node_modules/@upstash/context7-mcp/dist/index.js"
  "${PROMPTHUB_DIR}/mcps/node_modules/@wonderwhy-er/desktop-commander/dist/index.js"
  "${PROMPTHUB_DIR}/mcps/node_modules/@modelcontextprotocol/server-sequential-thinking/dist/index.js"
  "${PROMPTHUB_DIR}/mcps/node_modules/@modelcontextprotocol/server-memory/dist/index.js"
  "${PROMPTHUB_DIR}/mcps/node_modules/deepseek-reasoner-mcp/dist/index.js"
  "${PROMPTHUB_DIR}/mcps/node_modules/mcp-fetch/dist/stdio.js"
  "${PROMPTHUB_DIR}/mcps/obsidian-mcp-tools/bin/mcp-server"
)

for f in "${FILES[@]}"; do
  if [[ -f "${f}" ]]; then
    echo "FOUND: ${f}"
    ls -l "${f}" || true
    if [[ "${f}" == *.js ]]; then
      echo "  -> running 'node --check' on ${f}"
      node --check "${f}" 2>/dev/null || echo "  [WARN] Syntax check failed for ${f}"
    fi
  else
    echo "MISSING: ${f}"
  fi
done

echo ""
echo "Checking Python MCP servers..."
if [[ -f "${PROMPTHUB_DIR}/.venv/bin/activate" ]]; then
  # mcp-obsidian requires OBSIDIAN_API_KEY to import, so check if package is installed via pip
  if "${PROMPTHUB_DIR}/.venv/bin/pip" show mcp-obsidian &>/dev/null; then
    echo "FOUND: mcp-obsidian (Python package)"
    "${PROMPTHUB_DIR}/.venv/bin/pip" show mcp-obsidian | grep "Version:" || echo "  Version: unknown"
  else
    echo "MISSING: mcp-obsidian (Python package)"
  fi
else
  echo "MISSING: Python virtual environment at ${PROMPTHUB_DIR}/.venv"
fi

echo ""
echo "Suggested quick tests (use npx or command on PATH):"
echo "  npx -y @upstash/context7-mcp --help"
echo "  npx -y @wonderwhy-er/desktop-commander --help"
echo "  npx -y @modelcontextprotocol/server-sequential-thinking --help"
echo "  npx -y @modelcontextprotocol/server-memory --help"
echo "  npx -y deepseek-reasoner-mcp --help"
echo "  npx -y mcp-fetch --help"
echo "  ${PROMPTHUB_DIR}/scripts/obsidian-mcp-tools.sh --help"
echo "  ${PROMPTHUB_DIR}/scripts/mcp-obsidian-rest.sh --help"
