#!/bin/bash
#
# VS Code AgentHub Setup Script
#
# This script configures VS Code (Claude Code / Cline) to use AgentHub as an MCP server.
#
# Usage:
#   ./setup-vscode.sh [--global|--workspace] [--with-tasks]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_SETTINGS="$HOME/.vscode/settings.json"
WORKSPACE_SETTINGS=".vscode/settings.json"
EXAMPLE_SETTINGS="$SCRIPT_DIR/vscode-settings.json.example"
EXAMPLE_TASKS="$SCRIPT_DIR/tasks.json.example"

# Default mode
MODE="${1:-workspace}"
WITH_TASKS="${2:-}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
  log_error "VS Code 'code' command not found in PATH"
  echo ""
  echo "Install VS Code CLI:"
  echo "  1. Open VS Code"
  echo "  2. Cmd+Shift+P → 'Shell Command: Install code command in PATH'"
  echo ""
  exit 1
fi

log_success "VS Code CLI found"

# Determine target settings file
if [ "$MODE" = "--global" ]; then
  TARGET_SETTINGS="$GLOBAL_SETTINGS"
  TARGET_DIR="$(dirname "$GLOBAL_SETTINGS")"
  log_info "Using global settings: $TARGET_SETTINGS"
else
  TARGET_SETTINGS="$WORKSPACE_SETTINGS"
  TARGET_DIR=".vscode"
  log_info "Using workspace settings: $TARGET_SETTINGS"
fi

# Create directory if needed
mkdir -p "$TARGET_DIR"
log_success "Settings directory ready: $TARGET_DIR"

# Backup existing settings if present
if [ -f "$TARGET_SETTINGS" ]; then
  BACKUP_FILE="$TARGET_SETTINGS.backup-$(date +%Y%m%d-%H%M%S)"
  cp "$TARGET_SETTINGS" "$BACKUP_FILE"
  log_success "Existing settings backed up to: $BACKUP_FILE"

  # Merge with existing settings using jq if available
  if command -v jq &> /dev/null; then
    log_info "Merging with existing settings..."

    # Read existing and example settings
    EXISTING=$(cat "$TARGET_SETTINGS")
    EXAMPLE=$(cat "$EXAMPLE_SETTINGS")

    # Merge (example settings take precedence for AgentHub config)
    echo "$EXISTING" | jq -s '.[0] * .[1]' - <(echo "$EXAMPLE") > "$TARGET_SETTINGS"
    log_success "Settings merged successfully"
  else
    log_warning "jq not found - replacing settings entirely"
    cp "$EXAMPLE_SETTINGS" "$TARGET_SETTINGS"
    log_info "Backup contains your previous settings if needed"
  fi
else
  # No existing settings, just copy example
  cp "$EXAMPLE_SETTINGS" "$TARGET_SETTINGS"
  log_success "AgentHub settings installed"
fi

# Install tasks if requested
if [ "$WITH_TASKS" = "--with-tasks" ] || [ "$2" = "--with-tasks" ]; then
  TASKS_FILE="$TARGET_DIR/tasks.json"

  if [ -f "$TASKS_FILE" ]; then
    TASKS_BACKUP="$TASKS_FILE.backup-$(date +%Y%m%d-%H%M%S)"
    cp "$TASKS_FILE" "$TASKS_BACKUP"
    log_success "Existing tasks backed up to: $TASKS_BACKUP"
  fi

  cp "$EXAMPLE_TASKS" "$TASKS_FILE"
  log_success "AgentHub tasks installed to: $TASKS_FILE"
fi

# Verify AgentHub is running
echo ""
log_info "Verifying AgentHub connection..."
if curl -s --max-time 2 http://localhost:9090/health > /dev/null 2>&1; then
  log_success "AgentHub is running on localhost:9090"
else
  log_warning "AgentHub is not running or not reachable"
  echo ""
  echo "Start AgentHub with:"
  echo "  launchctl start com.agenthub.router"
  echo "Or:"
  echo "  cd ~/.local/share/agenthub && uvicorn router.main:app --port 9090"
fi

# Check for Claude Code or Cline extension
echo ""
log_info "Checking for VS Code extensions..."

if code --list-extensions | grep -q "anthropic.claude-code"; then
  log_success "Claude Code extension found"
elif code --list-extensions | grep -q "cline.cline"; then
  log_success "Cline extension found"
else
  log_warning "Neither Claude Code nor Cline extension found"
  echo ""
  echo "Install one of these extensions:"
  echo "  code --install-extension anthropic.claude-code"
  echo "  # OR"
  echo "  code --install-extension cline.cline"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Configuration installed:"
echo "  📄 Settings: $TARGET_SETTINGS"
if [ "$WITH_TASKS" = "--with-tasks" ] || [ "$2" = "--with-tasks" ]; then
  echo "  📋 Tasks: $TARGET_DIR/tasks.json"
fi
echo ""
echo "Next steps:"
echo "  1. Reload VS Code window:"
echo "     Cmd+Shift+P → 'Developer: Reload Window'"
echo ""
echo "  2. Verify MCP connection:"
echo "     - Check status bar for MCP indicator"
echo "     - Or use Claude Code command palette"
echo ""
echo "  3. Try AgentHub tasks:"
echo "     Cmd+Shift+P → 'Tasks: Run Task' → 'AgentHub: Health Check'"
echo ""
echo "  4. Test MCP tools:"
echo "     - Ask Claude Code to use context7 for documentation"
echo "     - Try file operations with desktop-commander"
echo ""

# Offer to reload VS Code
if [ "$MODE" != "--global" ]; then
  read -p "Reload VS Code window now? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Reloading VS Code..."
    # This opens a new window with the current directory
    code -r .
    log_success "Window reloaded"
  fi
fi
