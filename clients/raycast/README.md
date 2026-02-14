# Raycast Configuration

This folder contains configuration files for connecting Raycast to PromptHub.

## Files

### `raycast-mcp-servers.json.example`
Example configuration for Raycast MCP integration.

**Configuration:**
```json
{
  "servers": [{
    "id": "prompthub",
    "name": "PromptHub",
    "url": "http://localhost:9090",
    "type": "http",
    "enabled": true,
    "headers": {
      "X-Client-Name": "raycast"
    },
    "retries": 3,
    "timeout": 15000
  }]
}
```

### `setup-raycast.sh`
Automated setup script for configuring Raycast with PromptHub.

**Features:**
- Checks if Raycast is installed
- Creates config directory if needed
- Backs up existing configuration
- Installs PromptHub MCP configuration
- Verifies PromptHub is running
- Offers to restart Raycast automatically

**Usage:**
```bash
# Quick setup
cd ~/.local/share/prompthub/clients/raycast
./setup-raycast.sh

# With explicit backup
./setup-raycast.sh --backup
```

## Setup

Raycast connects to PromptHub via HTTP endpoints. See the Obsidian vault (`~/Vault/PromptHub/Integrations/Raycast.md`) for:

- Custom script commands
- MCP query shortcuts
- Action-oriented enhancements (optimized for CLI workflows)
- Raycast-specific configurations

## Enhancement Model

Raycast uses **DeepSeek-R1** for prompt enhancement with action-oriented focus:
- CLI commands and direct actions
- Concise responses (under 200 words)
- Optimized for quick workflows

This is configured in `../../enhancement-rules.json`.
