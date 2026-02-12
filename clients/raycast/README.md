# Raycast Configuration

This folder contains configuration files for connecting Raycast to AgentHub.

## Files

### `raycast-mcp-servers.json.example`
Example configuration for Raycast MCP integration.

**Configuration:**
```json
{
  "servers": [{
    "id": "agenthub",
    "name": "AgentHub",
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
Automated setup script for configuring Raycast with AgentHub.

**Features:**
- Checks if Raycast is installed
- Creates config directory if needed
- Backs up existing configuration
- Installs AgentHub MCP configuration
- Verifies AgentHub is running
- Offers to restart Raycast automatically

**Usage:**
```bash
# Quick setup
cd ~/.local/share/agenthub/clients/raycast
./setup-raycast.sh

# With explicit backup
./setup-raycast.sh --backup
```

## Setup

Raycast connects to AgentHub via HTTP endpoints. See the [Raycast integration guide](../../../guides/raycast-integration.md) for:

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
