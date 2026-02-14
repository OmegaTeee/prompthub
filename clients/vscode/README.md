# VS Code Configuration

This folder contains configuration files for connecting VS Code (Claude Code/Cline) to PromptHub.

## Files

### `vscode-settings.json.example`
Example VS Code settings for MCP integration via workspace settings.

**Location:** `.vscode/settings.json` in your workspace

```json
{
  "mcp.servers": {
    "prompthub": {
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
VS Code tasks for PromptHub operations.

**Available tasks:**
- Health Check - Verify router is running
- List MCP Servers - Show all servers and their status
- Start/Stop Router - Control PromptHub LaunchAgent
- View Dashboard - Open monitoring UI
- Clear Cache - Reset response cache
- Test Servers - Verify MCP server connectivity
- View Logs - Tail router logs in real-time

**Usage:** Copy to `.vscode/tasks.json` and run via `Cmd+Shift+P` → "Tasks: Run Task"

### `setup-vscode.sh`
Automated setup script for configuring VS Code with PromptHub.

**Features:**
- Checks if VS Code CLI is installed
- Creates settings directory if needed
- Backs up existing configuration
- Merges settings with existing config (using jq)
- Installs PromptHub MCP configuration
- Optionally installs VS Code tasks
- Verifies PromptHub is running
- Checks for Claude Code/Cline extension

**Usage:**
```bash
cd ~/.local/share/prompthub/clients/vscode

# Workspace setup (recommended)
./setup-vscode.sh --workspace

# With PromptHub tasks
./setup-vscode.sh --workspace --with-tasks

# Global setup (all workspaces)
./setup-vscode.sh --global --with-tasks
```

## Setup

VS Code connects to PromptHub via HTTP endpoints (not stdio). See the Obsidian vault (`~/Vault/PromptHub/Integrations/VS Code.md`) for:

- Workspace configuration
- Task definitions for PromptHub operations
- Debugging MCP connections
- Extension-specific settings

## Enhancement Model

VS Code uses **Qwen3-Coder** for prompt enhancement with code-first focus:
- Code examples before explanations
- Syntax-highlighted snippets
- IDE-optimized responses

This is configured in `../../enhancement-rules.json`.

## PromptHub Tasks

The configuration includes helpful VS Code tasks:

- **PromptHub: Health Check** - Verify router is running
- **PromptHub: List Servers** - See all MCP servers and status
- **PromptHub: Document Workspace** - Generate docs for current project

Access via `Cmd+Shift+P` → "Tasks: Run Task" → "PromptHub: ..."
