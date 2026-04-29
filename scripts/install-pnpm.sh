#!/usr/bin/env bash
set -euo pipefail

# install-pnpm.sh
# Enables corepack (bundled with Node), ensures pnpm is available, and prints install notes.

echo "Enabling corepack (if available)"
corepack enable || echo "corepack not available — skipping"

if command -v pnpm >/dev/null 2>&1; then
  echo "pnpm is already installed: $(pnpm -v)"
  exit 0
fi

echo "Installing pnpm globally (user-level)"
npm i -g pnpm --no-audit --no-fund || true

if command -v pnpm >/dev/null 2>&1; then
  echo "pnpm installed: $(pnpm -v)"
else
  echo "pnpm not found after install. Ensure npm global prefix is writable and in PATH."
fi
