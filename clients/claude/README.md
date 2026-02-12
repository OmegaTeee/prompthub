# Claude Desktop Configuration

This folder contains configuration files for connecting Claude Desktop to AgentHub.

## Files

### `claude-desktop-unified.json`
**Recommended configuration** using the unified MCP bridge that aggregates all 7 MCP servers.

```json
{
  "mcpServers": {
    "agenthub": {
      "command": "node",
      "args": ["/Users/visualval/.local/share/agenthub/mcps/agenthub-bridge.js"],
      "env": {
        "AGENTHUB_URL": "http://localhost:9090",
        "CLIENT_NAME": "claude-desktop"
      }
    }
  }
}
```

**Benefits:**
- Single MCP server entry (simpler configuration)
- Access to all 7 MCP servers through one interface
- Tools prefixed with server name (e.g., `context7_query-docs`)
- Native JSON-RPC 2.0 protocol (no protocol translation issues)

### `claude-desktop-config.json.example`
Example configuration showing curl-based approach for individual servers.

**When to use:**
- If you prefer granular control over which servers are enabled
- If you want to test individual server connections
- For debugging specific MCP server issues

### `claude_desktop_config.json` (symlink)
Symlink to your actual Claude Desktop configuration:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Note:** This is a convenience symlink for quick access. Your actual configuration should be edited at the real location.

### `setup-claude.sh`
Automated setup script for configuring Claude Desktop with AgentHub.

**Features:**
- Checks if Claude Desktop is installed
- Creates config directory if needed
- Backs up existing configuration
- Merges settings with existing config (using jq)
- Installs unified MCP bridge configuration
- Verifies AgentHub is running
- Checks for Node.js and MCP dependencies
- Offers to restart Claude Desktop automatically

**Usage:**
```bash
cd ~/.local/share/agenthub/clients/claude

# Quick setup
./setup-claude.sh

# With explicit backup
./setup-claude.sh --backup
```

## Setup

1. Choose your configuration approach (unified is recommended)
2. Copy the desired config to your Claude Desktop config location:
   ```bash
   cp claude-desktop-unified.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
3. Restart Claude Desktop
4. Verify connection in Claude Desktop settings

## Recommended Custom Instructions

For optimal tool usage experience, add these custom instructions in Claude Desktop settings:

```txt
Tool Usage Policy:
- Use MCP tools automatically when they're clearly useful for the task
- Mention when you're accessing tools (e.g., "Using context7 to fetch docs...")
- Always request explicit permission before modifying system files or data
- Prefer built-in tools for file operations, documentation lookup, and web requests
```

See [guides/claude-desktop-integration.md](../../../guides/claude-desktop-integration.md) for full setup instructions.
