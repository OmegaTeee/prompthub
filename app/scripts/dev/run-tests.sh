#!/bin/bash
#
# Test Runner for PromptHub
#
# Usage:
#   ./scripts/run-tests.sh               # Run all tests
#   ./scripts/run-tests.sh unit          # Run only unit tests
#   ./scripts/run-tests.sh integration   # Run only integration tests
#   ./scripts/run-tests.sh coverage      # Run with coverage report

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 PromptHub Test Runner"
echo "======================="

# Check if in virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Not in a virtual environment${NC}"
    echo "   Run: source .venv/bin/activate"
    echo ""
fi

# Determine test mode
MODE=${1:-all}

case "${MODE}" in
    unit)
        echo "Running unit tests only..."
        pytest tests/ -v -m "not integration" --tb=short
        ;;

    integration)
        echo "Running integration tests..."
        echo ""
        echo -e "${YELLOW}Prerequisites:${NC}"
        echo "  ✓ PromptHub must be running on localhost:9090"
        echo "  ✓ All MCP servers should be started"
        echo "  ✓ Ollama should be running (for enhancement tests)"
        echo ""

        # Check if PromptHub is running
        if ! curl -s http://localhost:9090/health > /dev/null 2>&1; then
            echo -e "${RED}❌ PromptHub is not running!${NC}"
            echo "   Start it with: uvicorn router.main:app --port 9090"
            exit 1
        fi

        echo -e "${GREEN}✓ PromptHub is running${NC}"
        echo ""

        pytest tests/integration/ -v --tb=short
        ;;

    coverage)
        echo "Running tests with coverage..."
        pytest tests/ -v --cov=router --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated:${NC} htmlcov/index.html"
        echo "   Open with: open htmlcov/index.html"
        ;;

    quick)
        echo "Running quick tests (unit only, no slow tests)..."
        pytest tests/ -v -m "not integration and not slow" --tb=short
        ;;

    all)
        echo "Running all tests..."
        echo ""

        # Check if PromptHub is running for integration tests
        if curl -s http://localhost:9090/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PromptHub is running - will run integration tests${NC}"
            pytest tests/ -v --tb=short
        else
            echo -e "${YELLOW}⚠️  PromptHub not running - skipping integration tests${NC}"
            pytest tests/ -v -m "not integration" --tb=short
        fi
        ;;

    *)
        echo "Unknown mode: ${MODE}"
        echo ""
        echo "Usage:"
        echo "  ./scripts/run-tests.sh [mode]"
        echo ""
        echo "Modes:"
        echo "  all          - Run all tests (default)"
        echo "  unit         - Run only unit tests"
        echo "  integration  - Run only integration tests"
        echo "  coverage     - Run with coverage report"
        echo "  quick        - Run quick tests only"
        exit 1
        ;;
esac

# Exit with pytest's exit code
exit $?
