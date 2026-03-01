#!/usr/bin/env zsh
# =============================================================================
# PromptHub test runner
# Usage:
#   ./scripts/test.sh              # unit tests only (fast, no server needed)
#   ./scripts/test.sh unit         # same
#   ./scripts/test.sh integration  # integration tests (requires live server)
#   ./scripts/test.sh all          # everything
#   ./scripts/test.sh coverage     # unit tests + HTML coverage report
#   ./scripts/test.sh watch        # re-run unit tests on file change
# =============================================================================

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$APP_DIR/.venv/bin/activate"

# Colours
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

log()  { echo "${GREEN}==>${NC} $*"; }
warn() { echo "${YELLOW}  >${NC} $*"; }
die()  { echo "${RED}✗ $*${NC}" >&2; exit 1; }

# Activate venv
[[ -f "$VENV" ]] || die "venv not found at $VENV — run: cd $APP_DIR && python3 -m venv .venv && pip install -e ."
source "$VENV"

cd "$APP_DIR"

MODE="${1:-unit}"

case "$MODE" in

  unit)
    log "Running unit tests..."
    python3 -m pytest tests/unit/ -v --tb=short
    ;;

  integration)
    warn "Integration tests require a live PromptHub server on :9090"
    warn "Start it with: cd $APP_DIR && uvicorn router.main:app --port 9090"
    echo ""
    python3 -m pytest tests/integration/ -v --tb=short
    ;;

  all)
    log "Running full test suite..."
    warn "Integration tests may fail if server is not running"
    echo ""
    python3 -m pytest tests/ -v --tb=short \
      --ignore=tests/integration \
      -q
    echo ""
    log "Running integration tests separately (failures expected without server)..."
    python3 -m pytest tests/integration/ --tb=line -q || true
    ;;

  coverage)
    log "Running unit tests with coverage..."
    python3 -m pytest tests/unit/ \
      --cov=router \
      --cov-report=term-missing \
      --cov-report=html:htmlcov \
      --tb=short
    echo ""
    log "HTML report: $APP_DIR/htmlcov/index.html"
    echo "  open htmlcov/index.html"
    ;;

  watch)
    if ! command -v watchexec &>/dev/null; then
      warn "watchexec not found — install with: brew install watchexec"
      die "Cannot run watch mode"
    fi
    log "Watching for changes (unit tests)..."
    watchexec \
      --exts py \
      --watch router \
      --watch tests/unit \
      -- python3 -m pytest tests/unit/ -v --tb=short -q
    ;;

  *)
    echo "Usage: $0 [unit|integration|all|coverage|watch]"
    exit 1
    ;;

esac
