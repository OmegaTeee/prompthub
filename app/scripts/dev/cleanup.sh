#!/bin/bash
# cleanup.sh - Remove temporary files, cache, and build artifacts
# Usage: ./scripts/dev/cleanup.sh [--dry-run]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Dry run flag
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}🔍 DRY RUN MODE - No files will be deleted${NC}\n"
fi

# Change to project root
cd "$(dirname "$0")/../.."

echo -e "${BLUE}🧹 AgentHub Cleanup Script${NC}\n"

# Track stats
TOTAL_FILES=0
TOTAL_SIZE=0

# Function to remove files/directories
cleanup() {
    local pattern=$1
    local description=$2
    local find_type=$3  # 'd' for directories, 'f' for files

    echo -e "${YELLOW}Cleaning: ${description}${NC}"

    if [[ "$find_type" == "d" ]]; then
        # Count and measure directories
        local count=$(find . -type d -name "$pattern" -not -path "./.venv/*" -not -path "./mcps/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
        local size=$(find . -type d -name "$pattern" -not -path "./.venv/*" -not -path "./mcps/node_modules/*" -exec du -sk {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')

        if [[ "$count" -gt 0 ]]; then
            echo "  Found: $count directories (${size}KB)"
            TOTAL_FILES=$((TOTAL_FILES + count))
            TOTAL_SIZE=$((TOTAL_SIZE + size))

            if [[ "$DRY_RUN" == false ]]; then
                find . -type d -name "$pattern" -not -path "./.venv/*" -not -path "./mcps/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
                echo -e "  ${GREEN}✓ Removed${NC}"
            fi
        else
            echo "  No files found"
        fi
    else
        # Count and measure files
        local count=$(find . -type f -name "$pattern" -not -path "./.venv/*" -not -path "./mcps/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
        local size=$(find . -type f -name "$pattern" -not -path "./.venv/*" -not -path "./mcps/node_modules/*" -exec du -sk {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')

        if [[ "$count" -gt 0 ]]; then
            echo "  Found: $count files (${size}KB)"
            TOTAL_FILES=$((TOTAL_FILES + count))
            TOTAL_SIZE=$((TOTAL_SIZE + size))

            if [[ "$DRY_RUN" == false ]]; then
                find . -type f -name "$pattern" -not -path "./.venv/*" -not -path "./mcps/node_modules/*" -delete 2>/dev/null || true
                echo -e "  ${GREEN}✓ Removed${NC}"
            fi
        else
            echo "  No files found"
        fi
    fi
    echo ""
}

# Python cache files
cleanup "__pycache__" "Python bytecode cache" "d"
cleanup "*.pyc" "Python compiled files" "f"
cleanup "*.pyo" "Python optimized files" "f"

# macOS metadata
cleanup ".DS_Store" "macOS metadata files" "f"
cleanup ".AppleDouble" "AppleDouble files" "d"

# Editor temporary files
cleanup "*.swp" "Vim swap files" "f"
cleanup "*.swo" "Vim swap files (old)" "f"
cleanup "*~" "Editor backup files" "f"

# Temporary files
cleanup "*.tmp" "Temporary files" "f"
cleanup "*.temp" "Temporary files" "f"

# Test cache
echo -e "${YELLOW}Cleaning: pytest cache${NC}"
if [[ -d ".pytest_cache" ]]; then
    size=$(du -sk .pytest_cache 2>/dev/null | awk '{print $1}')
    echo "  Found: .pytest_cache (${size}KB)"
    TOTAL_SIZE=$((TOTAL_SIZE + size))
    TOTAL_FILES=$((TOTAL_FILES + 1))

    if [[ "$DRY_RUN" == false ]]; then
        rm -rf .pytest_cache
        echo -e "  ${GREEN}✓ Removed${NC}"
    fi
else
    echo "  No cache found"
fi
echo ""

# Old logs in /tmp
echo -e "${YELLOW}Cleaning: temporary log files${NC}"
if [[ -f "/tmp/agenthub-router.log" ]]; then
    size=$(du -sk /tmp/agenthub-router.log 2>/dev/null | awk '{print $1}')
    echo "  Found: /tmp/agenthub-router.log (${size}KB)"
    TOTAL_SIZE=$((TOTAL_SIZE + size))
    TOTAL_FILES=$((TOTAL_FILES + 1))

    if [[ "$DRY_RUN" == false ]]; then
        rm -f /tmp/agenthub-router.log
        echo -e "  ${GREEN}✓ Removed${NC}"
    fi
else
    echo "  No temp logs found"
fi
echo ""

# Node module logs
echo -e "${YELLOW}Cleaning: node module setup logs${NC}"
node_logs=$(find mcps/node_modules -name "setup.log" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$node_logs" -gt 0 ]]; then
    size=$(find mcps/node_modules -name "setup.log" -exec du -sk {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
    echo "  Found: $node_logs setup logs (${size}KB)"
    TOTAL_SIZE=$((TOTAL_SIZE + size))
    TOTAL_FILES=$((TOTAL_FILES + node_logs))

    if [[ "$DRY_RUN" == false ]]; then
        find mcps/node_modules -name "setup.log" -delete 2>/dev/null || true
        echo -e "  ${GREEN}✓ Removed${NC}"
    fi
else
    echo "  No setup logs found"
fi
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}Would remove:${NC}"
else
    echo -e "${GREEN}Cleanup complete!${NC}"
fi
echo "  Files/directories: $TOTAL_FILES"
echo "  Space saved: $(echo "scale=2; $TOTAL_SIZE/1024" | bc)MB"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "\n${YELLOW}To actually delete these files, run:${NC}"
    echo "  ./scripts/dev/cleanup.sh"
fi

echo ""
echo -e "${GREEN}✨ Repository cleanup finished!${NC}"
