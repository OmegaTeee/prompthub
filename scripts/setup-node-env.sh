#!/usr/bin/env bash
set -euo pipefail

# setup-node-env.sh
# Move npm global prefix to a user-writable location, enable corepack/pnpm,
# and add PATH exports to the user's shell profile (safe, idempotent, backed up).

PROFILE="$HOME/.zshrc"
if [ -n "${SHELL-}" ] && [[ "$SHELL" == */bash ]]; then
  PROFILE="$HOME/.bashrc"
fi

BACKUP="$PROFILE.prompthub.bak.$(date +%s)"
echo "Backing up $PROFILE -> $BACKUP"
cp -- "$PROFILE" "$BACKUP" 2>/dev/null || true

NPM_PREFIX="$HOME/.local/share/npm"
mkdir -p "$NPM_PREFIX"

echo "Setting npm global prefix to $NPM_PREFIX"
npm config set prefix "$NPM_PREFIX"

BIN_LINE="export PATH=\"$NPM_PREFIX/bin:\$PATH\""

if ! grep -qxF "$BIN_LINE" "$PROFILE" 2>/dev/null; then
  echo "Adding npm global bin to $PROFILE"
  printf "\n# Added by PromptHub setup-node-env\n%s\n" "$BIN_LINE" >> "$PROFILE"
else
  echo "PATH line already present in $PROFILE"
fi

echo "Enabling corepack and installing pnpm (user-level)"
corepack enable || true
if command -v pnpm >/dev/null 2>&1; then
  echo "pnpm already installed"
else
  npm i -g pnpm --no-audit --no-fund || true
fi

echo
echo "Done. Restart your shell or run: source $PROFILE"
