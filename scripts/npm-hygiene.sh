#!/usr/bin/env bash
set -euo pipefail

# npm-hygiene.sh
# Useful maintenance tasks: verify/clean cache, list large cache entries, and run audit.

usage() {
  cat <<'EOF'
Usage: npm-hygiene.sh [command]

Commands:
  verify     Run npm cache verify and npm doctor
  clean      Force clean npm cache
  list-cache Show sizes of top cache directories
  audit      Run npm audit and npm audit fix
  help       Show this message
EOF
}

cmd=${1-verify}
case "$cmd" in
  verify)
    echo "Verifying npm cache and running npm doctor..."
    npm cache verify
    npm doctor
    ;;
  clean)
    echo "Cleaning npm cache (force)..."
    npm cache clean --force
    rm -rf "$HOME/.npm/_cacache" || true
    npm cache verify || true
    ;;
  list-cache)
    echo "Top entries in ~/.npm/_cacache by disk usage:"
    du -sh "$HOME/.npm/_cacache"/* 2>/dev/null | sort -hr | head -n 20 || true
    ;;
  audit)
    echo "Running npm audit..."
    npm audit || true
    echo "Attempting npm audit fix (may change package-lock.json)"
    npm audit fix || true
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage
    exit 2
    ;;
esac
