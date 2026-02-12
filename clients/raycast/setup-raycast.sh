#!/bin/bash
#
# Raycast AgentHub Setup Script
#
# This script configures Raycast to use AgentHub as an MCP server.
#
# Usage:
#   ./setup-raycast.sh [--backup]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/Library/Application Support/com.raycast.macos"
CONFIG_FILE="$CONFIG_DIR/mcp-servers.json"
EXAMPLE_CONFIG="$SCRIPT_DIR/raycast-mcp-servers.json.example"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Check if Raycast is installed
if ! command -v open &> /dev/null || ! [ -d "/Applications/Raycast.app" ]; then
  log_error "Raycast is not installed"
  echo "Please install Raycast from: https://raycast.com"
  exit 1
fi

log_success "Raycast found"

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"
log_success "Config directory ready: $CONFIG_DIR"

# Backup existing config if requested
if [ "${1:-}" = "--backup" ] || [ -f "$CONFIG_FILE" ]; then
  if [ -f "$CONFIG_FILE" ]; then
    BACKUP_FILE="$CONFIG_FILE.backup-$(date +%Y%m%d-%H%M%S)"
    cp "$CONFIG_FILE" "$BACKUP_FILE"
    log_success "Existing config backed up to: $BACKUP_FILE"
  fi
fi

# Copy example config
if [ -f "$EXAMPLE_CONFIG" ]; then
  cp "$EXAMPLE_CONFIG" "$CONFIG_FILE"
  log_success "AgentHub configuration installed"
else
  log_error "Example config not found: $EXAMPLE_CONFIG"
  exit 1
fi

# Verify AgentHub is running
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

# Prompt to restart Raycast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Restart Raycast:"
echo "     killall Raycast && open -a Raycast"
echo ""
echo "  2. Verify connection:"
echo "     - Open Raycast (Cmd+Space)"
echo "     - Type 'AI Settings'"
echo "     - Check MCP Servers → AgentHub should show '✅ Connected'"
echo ""
echo "  3. Test it out:"
echo "     - Use AI commands with AgentHub tools"
echo "     - Try: 'context7: React hooks documentation'"
echo ""

# Ask if user wants to restart Raycast now
read -p "Restart Raycast now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  log_success "Restarting Raycast..."
  killall Raycast 2>/dev/null || true
  sleep 1
  open -a Raycast
  log_success "Raycast restarted"
fi
