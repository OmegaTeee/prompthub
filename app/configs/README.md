# PromptHub Configuration Files

This folder contains all configuration files for PromptHub and client integrations.

## Directory Structure

```
configs/
├── README.md                              # This file
├── enhancement-rules.json                 # PromptHub: Prompt enhancement rules
├── mcp-servers.json                       # PromptHub: MCP server registry
├── logrotate.conf                         # System: Log rotation (Linux)
└── logrotate-macos.conf                   # System: Log rotation (macOS)
```

> **Note:** Desktop client configurations (Claude Desktop, Raycast, MCP Inspector) live in [`mcps/configs/`](../../mcps/configs/README.md), co-located with the MCP bridge.

## Configuration Types

### ⚙️ PromptHub Configurations
Core PromptHub router settings:
- **`enhancement-rules.json`** - Per-client Ollama models and system prompts
- **`mcp-servers.json`** - MCP server lifecycle (command, args, auto_start)
**When to modify:** Adding MCP servers or changing enhancement behavior.

### 🔧 System Configurations (root)
Infrastructure and logging:
- **`logrotate.conf`** - Log file rotation and archival
- **`logrotate-macos.conf`** - macOS-specific log rotation

**When to modify:** Adjusting log retention policies or disk space management.

### Common Tasks

**Add a new MCP server:**

```bash
# Edit the registry
vim configs/mcp-servers.json

# Add entry like:
{
  "my-server": {
    "command": "npx",
    "args": ["-y", "@org/my-mcp-server"],
    "auto_start": true,
    "restart_on_failure": true,
    "max_restart_delay_seconds": 300
  }
}
```

**Change enhancement model:**

```bash
# Edit enhancement rules
vim configs/enhancement-rules.json

# Modify client-specific model:
{
  "vscode": {
    "model": "qwen2.5-coder:latest",  # Change to your preferred model
    "system_prompt": "..."
  }
}
```

**Configure credentials:**

Credentials are stored in macOS Keychain and referenced inline in `mcp-servers.json`:

```json
{
  "env": {
    "MY_API_KEY": {
      "source": "keyring",
      "service": "prompthub",
      "key": "my_api_key"
    }
  }
}
```

Store a credential:

```bash
python3 -c "import keyring; keyring.set_password('prompthub', 'my_api_key', 'YOUR_VALUE')"
```

## Configuration Philosophy

This organization separates:

1. **Client concerns** (how apps connect) → `mcps/configs/`
2. **Router concerns** (how PromptHub behaves) → `app/configs/`
3. **System concerns** (logging, OS integration) → `app/configs/`

This makes it easy to:
- ✅ Add new clients without touching PromptHub config
- ✅ Modify PromptHub behavior without breaking clients
- ✅ Share client configs with team members
- ✅ Version control client and router configs separately

## Environment Variables

PromptHub supports environment variable overrides:

```bash
# Override router port
ROUTER_PORT=8080 uvicorn router.main:app

# Override MCP config location
MCP_CONFIG_PATH=/custom/path/mcp-servers.json uvicorn router.main:app

# Override enhancement config
ENHANCEMENT_CONFIG_PATH=/custom/path/enhancement-rules.json uvicorn router.main:app
```

## Best Practices

### Version Control

```bash
# Track PromptHub configs
git add configs/enhancement-rules.json
git add configs/mcp-servers.json

# Ignore local config overrides
echo "app/configs/*.local.json" >> .gitignore
```

### Secrets Management

Credentials live in macOS Keychain, not in config files. The `mcp-servers.json` `env` blocks use `{"source": "keyring"}` references that are resolved at server startup — no secrets on disk.

### Backup

```bash
# Backup all configs
tar -czf prompthub-configs-$(date +%Y%m%d).tar.gz configs/

# Restore
tar -xzf prompthub-configs-20260130.tar.gz
```

