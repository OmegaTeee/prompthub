# VS Code Configuration

This folder contains configuration files for connecting VS Code (Claude Code/Cline) to AgentHub.

## Files

### `vscode-settings.json.example`
Example VS Code settings for MCP integration via workspace settings.

**Location:** `.vscode/settings.json` in your workspace

```json
{
  "mcp.servers": {
    "agenthub": {
      "type": "http",
      "url": "http://localhost:9090",
      "headers": {
        "X-Client-Name": "vscode"
      }
    }
  }
}
```

### `vscode.json`
Full VS Code workspace settings with MCP integration and editor preferences.

**Includes:**
- MCP server configuration via HTTP
- Auto-connect and caching settings
- Editor formatting preferences
- File associations
- Extension recommendations

### `tasks.json.example`
VS Code tasks for AgentHub operations.

**Available tasks:**
- Health Check - Verify router is running
- List MCP Servers - Show all servers and their status
- Start/Stop Router - Control AgentHub LaunchAgent
- View Dashboard - Open monitoring UI
- Clear Cache - Reset response cache
- Test Servers - Verify MCP server connectivity
- View Logs - Tail router logs in real-time

**Usage:** Copy to `.vscode/tasks.json` and run via `Cmd+Shift+P` → "Tasks: Run Task"

### `setup-vscode.sh`
Automated setup script for configuring VS Code with AgentHub.

**Features:**
- Checks if VS Code CLI is installed
- Creates settings directory if needed
- Backs up existing configuration
- Merges settings with existing config (using jq)
- Installs AgentHub MCP configuration
- Optionally installs VS Code tasks
- Verifies AgentHub is running
- Checks for Claude Code/Cline extension

**Usage:**
```bash
cd ~/.local/share/agenthub/clients/vscode

# Workspace setup (recommended)
./setup-vscode.sh --workspace

# With AgentHub tasks
./setup-vscode.sh --workspace --with-tasks

# Global setup (all workspaces)
./setup-vscode.sh --global --with-tasks
```

## Setup

VS Code connects to AgentHub via HTTP endpoints (not stdio). See the [VS Code integration guide](../../../guides/vscode-integration.md) for:

- Workspace configuration
- Task definitions for AgentHub operations
- Debugging MCP connections
- Extension-specific settings

## Enhancement Model

VS Code uses **Qwen3-Coder** for prompt enhancement with code-first focus:
- Code examples before explanations
- Syntax-highlighted snippets
- IDE-optimized responses

This is configured in `../../enhancement-rules.json`.

## AgentHub Tasks

The configuration includes helpful VS Code tasks:

- **AgentHub: Health Check** - Verify router is running
- **AgentHub: List Servers** - See all MCP servers and status
- **AgentHub: Document Workspace** - Generate docs for current project

Access via `Cmd+Shift+P` → "Tasks: Run Task" → "AgentHub: ..."
