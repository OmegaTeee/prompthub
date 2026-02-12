#!/bin/bash
#
# Claude Desktop AgentHub Setup Script
#
# This script configures Claude Desktop to use AgentHub's unified MCP bridge.
#
# Usage:
#   ./setup-claude.sh [--backup]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${HOME}/Library/Application Support/Claude/claude_desktop_config.json"
EXAMPLE_CONFIG="${SCRIPT_DIR}/claude-desktop-unified.json"

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

# Check if Claude Desktop is installed
if ! [[ -d "/Applications/Claude.app" ]]; then
  log_error "Claude Desktop is not installed"
  echo "Please install Claude Desktop from: https://claude.ai/download"
  exit 1
fi

log_success "Claude Desktop found"

# Create config directory if it doesn't exist
CONFIG_DIR="$(dirname "${CONFIG_FILE}")"
mkdir -p "${CONFIG_DIR}"
log_success "Config directory ready: ${CONFIG_DIR}"

# Backup existing config if present
if [[ -f "${CONFIG_FILE}" ]]; then
  BACKUP_FILE="${CONFIG_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
  cp "${CONFIG_FILE}" "${BACKUP_FILE}"
  log_success "Existing config backed up to: ${BACKUP_FILE}"

  # Check if user wants to merge with existing config
  if command -v jq &> /dev/null; then
    log_info "jq found - can merge with existing mcpServers"
    read -p "Merge with existing config? (y/n) " -n 1 -r
    echo
    if [[ ${REPLY} =~ ^[Yy]$ ]]; then
      # Read existing and example configs
      EXISTING=$(cat "${CONFIG_FILE}")
      EXAMPLE=$(cat "${EXAMPLE_CONFIG}")

      # Merge mcpServers
      echo "${EXISTING}" | jq --argjson example "$(cat "${EXAMPLE_CONFIG}")" \
        '.mcpServers = (.mcpServers // {}) + $example.mcpServers' > "${CONFIG_FILE}"
      log_success "Configs merged successfully"
    else
      cp "${EXAMPLE_CONFIG}" "${CONFIG_FILE}"
      log_info "Using unified config (backup contains previous settings)"
    fi
  else
    log_warning "jq not found - replacing config entirely"
    cp "${EXAMPLE_CONFIG}" "${CONFIG_FILE}"
    log_info "Backup contains your previous settings if needed"
  fi
else
  # No existing config, just copy example
  cp "${EXAMPLE_CONFIG}" "${CONFIG_FILE}"
  log_success "AgentHub configuration installed"
fi

# Verify AgentHub is running
echo ""
log_info "Verifying AgentHub connection..."
if curl -s --max-time 2 http://localhost:9090/health > /dev/null 2>&1; then
  log_success "AgentHub is running on localhost:9090"

  # Check server count
  SERVER_COUNT=$(curl -s http://localhost:9090/servers | jq 'length' 2>/dev/null || echo "unknown")
  if [[ "${SERVER_COUNT}" != "unknown" ]]; then
    log_success "Found ${SERVER_COUNT} MCP servers"
  fi
else
  log_warning "AgentHub is not running or not reachable"
  echo ""
  echo "Start AgentHub with:"
  echo "  launchctl start com.agenthub.router"
  echo "Or:"
  echo "  cd ~/.local/share/agenthub && uvicorn router.main:app --port 9090"
fi

# Check if Node.js is available (required for the MCP bridge)
echo ""
log_info "Checking dependencies..."
if ! command -v node &> /dev/null; then
  log_error "Node.js is not installed"
  echo "Install Node.js (required for MCP bridge):"
  echo "  brew install node"
  exit 1
fi

NODE_VERSION=$(node --version)
log_success "Node.js found: ${NODE_VERSION}"

# Verify MCP bridge script exists
BRIDGE_SCRIPT="${HOME}/.local/share/agenthub/mcps/agenthub-bridge.js"
if [[ ! -f "${BRIDGE_SCRIPT}" ]]; then
  log_error "MCP bridge script not found: ${BRIDGE_SCRIPT}"
  echo "Please ensure AgentHub is properly installed"
  exit 1
fi

log_success "MCP bridge script found"

# Check if dependencies are installed
BRIDGE_DIR="$(dirname "${BRIDGE_SCRIPT}")"
if [[ ! -d "${BRIDGE_DIR}/node_modules/@modelcontextprotocol" ]]; then
  log_warning "MCP SDK dependencies not found"
  echo "Installing dependencies..."

  cd "${BRIDGE_DIR}"
  npm install

  if [[ $? -eq 0 ]]; then
    log_success "Dependencies installed"
  else
    log_error "Failed to install dependencies"
    exit 1
  fi
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Configuration installed:"
echo "  📄 ${CONFIG_FILE}"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Desktop:"
echo "     osascript -e 'quit app \"Claude\"' && open -a \"Claude\""
echo ""
echo "  2. Verify MCP connection:"
echo "     - Open Claude Desktop"
echo "     - Look for MCP badge at bottom: 🔌 agenthub"
echo "     - Should show: '7 tools available'"
echo ""
echo "  3. Test MCP tools:"
echo "     - Ask: 'What MCP tools are available?'"
echo "     - Try: 'Use context7 to find React hooks documentation'"
echo ""
echo "  4. Optional: Set up custom instructions"
echo "     - Settings → Custom Instructions"
echo "     - Add tool usage policy (see README.md)"
echo ""

# Offer to restart Claude Desktop
read -p "Restart Claude Desktop now? (y/n) " -n 1 -r
echo
if [[ ${REPLY} =~ ^[Yy]$ ]]; then
  log_info "Restarting Claude Desktop..."
  osascript -e 'quit app "Claude"' 2>/dev/null || true
  sleep 2
  open -a "Claude"
  log_success "Claude Desktop restarted"
fi
