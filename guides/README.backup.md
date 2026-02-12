# AgentHub User Guides

> **Complete documentation for installing, configuring, and using AgentHub as your centralized MCP router**

---

## Overview

AgentHub is a **centralized MCP (Model Context Protocol) router** for macOS that provides:

- **Unified Access** - Connect multiple desktop apps (Claude Desktop, VS Code, Raycast) to 7+ MCP servers through a single endpoint
- **Prompt Enhancement** - Automatically improve prompts with Ollama (DeepSeek-R1, Qwen3-Coder)
- **Auto-Restart** - MCP servers automatically restart if they crash
- **Intelligent Caching** - Faster responses through L1 in-memory cache
- **Audit Logging** - Production-grade audit trails for all requests

---

## Quick Start

**New to AgentHub?** Start here:

1. **[Getting Started](getting-started.md)** - Install and verify AgentHub
2. **[LaunchAgent Setup](launchagent-setup.md)** - Auto-start AgentHub on login
3. **[Keychain Setup](keychain-setup.md)** - Secure credential storage

**Then integrate your favorite apps:**

1. **[Claude Desktop Integration](claude-desktop-integration.md)** - Connect Claude Desktop
2. **[VS Code Integration](vscode-integration.md)** - Connect VS Code / Cline / Claude Code
3. **[Raycast Integration](raycast-integration.md)** - Connect Raycast launcher

**Finally, test everything works:**

1. **[Testing Integrations](testing-integrations.md)** - Comprehensive test suite

---

## Documentation Index

### Installation & Setup

| Guide | Description |
|-------|-------------|
| **[Getting Started](getting-started.md)** | Quick start guide, installation, and health checks |
| **[Docker Guide](docker-guide.md)** | Running AgentHub with Docker Compose |
| **[LaunchAgent Setup](launchagent-setup.md)** | Auto-start AgentHub on macOS login |
| **[Keychain Setup](keychain-setup.md)** | Secure credential management with macOS Keychain |
| **[Keyring Migration](keyring-migration-guide.md)** | Migrate from security CLI to Python keyring |

### Client Integrations

| Client | Guide | Key Features |
|--------|-------|-------------|
| **Claude Desktop** | [claude-desktop-integration.md](claude-desktop-integration.md) | DeepSeek-R1 enhancement, structured reasoning, 7 MCP servers |
| **VS Code** | [vscode-integration.md](vscode-integration.md) | Qwen3-Coder enhancement, code-first responses, file operations |
| **Raycast** | [raycast-integration.md](raycast-integration.md) | Action-oriented CLI commands, under 200 words, quick docs |
| **All Apps** | [app-configs.md](app-configs.md) | Quick configuration reference for all supported clients |

### Testing & Validation

| Guide | Description |
|-------|-------------|
| **[Testing Integrations](testing-integrations.md)** | Comprehensive test procedures for all clients |

### Advanced Integrations

| Guide | Description |
|-------|-------------|
| **[Figma Integration](figma-integration.md)** | Design-to-code workflows with Figma MCP |
| **[ComfyUI Integration](comfyui-integration.md)** | Image generation workflows |

### Reference

| Guide | Description |
|-------|-------------|
| **[Comparison Table](comparison-table.md)** | AgentHub vs alternatives, decision framework |
| **[Keyring vs Security CLI](keyring-vs-security-cli.md)** | Credential storage comparison |

---

## Integration Quick Reference

### Claude Desktop

```bash
# Config location
~/Library/Application Support/Claude/claude_desktop_config.json

# Add AgentHub
jq '.mcpServers["agenthub"] = {
  "command": "curl",
  "args": [
    "-s",
    "-X",
    "POST",
    "http://localhost:9090/mcp/context7/tools/call",
    "-H",
    "Content-Type: application/json",
    "-H",
    "X-Client-Name: claude-desktop",
    "-d",
    "@-"
  ]
}' ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart
osascript -e 'quit app "Claude"' && open -a "Claude"
```

**Enhancement:** DeepSeek-R1:latest with structured reasoning
**Note:** Uses curl to bridge stdio (Claude Desktop) to HTTP (AgentHub)

---

### VS Code (Claude Code / Cline)

```bash
# Config location
~/.vscode/settings.json

# Add AgentHub
{
  "claude.mcp.servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "transport": "http",
      "headers": {"X-Client-Name": "vscode"}
    }
  }
}

# Reload
Cmd+Shift+P → "Developer: Reload Window"
```

**Enhancement:** Qwen3-Coder:latest with code-first responses

---

### Raycast

```bash
# Config location
~/Library/Application Support/com.raycast.macos/mcp-servers.json

# Add AgentHub
{
  "servers": [{
    "id": "agenthub",
    "name": "AgentHub",
    "url": "http://localhost:9090",
    "type": "http",
    "headers": {"X-Client-Name": "raycast"}
  }]
}

# Restart
killall Raycast && open -a Raycast
```

**Enhancement:** DeepSeek-R1:latest with action-oriented CLI commands

---

## Available MCP Servers

AgentHub provides access to **7 MCP servers** by default:

| Server | Description | Use Case |
|--------|-------------|----------|
| **context7** | Documentation fetching | "Use context7: React hooks" |
| **desktop-commander** | File operations & terminal | "Use desktop-commander: List files" |
| **sequential-thinking** | Step-by-step reasoning | "Use sequential-thinking: Plan project" |
| **memory** | Cross-session context | "Use memory: Remember my preferences" |
| **deepseek-reasoner** | Local AI reasoning | "Use deepseek-reasoner: Solve problem" |
| **fetch** | Web requests | "Use fetch: Get latest news" |
| **obsidian** | Note management | "Use obsidian: Search notes" |

---

## Client-Specific Features

### Prompt Enhancement

Each client gets **customized prompt enhancement**:

| Client | Model | Enhancement Style |
|--------|-------|-------------------|
| Claude Desktop | DeepSeek-R1:latest | Structured responses with clear reasoning |
| VS Code | Qwen3-Coder:latest | Code-first, minimal prose, file paths |
| Raycast | DeepSeek-R1:latest | Action-oriented, CLI commands, <200 words |

Configured in: `~/.local/share/agenthub/configs/enhancement-rules.json`

### Response Caching

- **L1 Cache**: In-memory, exact match, LRU eviction
- **Cache TTL**: 1 hour (configurable)
- **Shared**: All clients benefit from cached responses

**Example:**
- First request (Claude Desktop): ~2-3 seconds
- Second request (VS Code, same query): <100ms

---

## Common Tasks

### Check AgentHub Health

```bash
curl http://localhost:9090/health
```

**Expected:**

```json
{
  "status": "healthy",
  "router": "up",
  "ollama": "up",
  "servers": {
    "total": 7,
    "running": 7,
    "stopped": 0,
    "failed": 0
  }
}
```

### List MCP Servers

```bash
curl http://localhost:9090/servers | jq
```

### View Dashboard

```bash
open http://localhost:9090/dashboard
```

### Restart a Server

```bash
curl -X POST http://localhost:9090/servers/<server-name>/restart
```

### Clear Cache

```bash
curl -X POST http://localhost:9090/dashboard/actions/clear-cache
```

### View Audit Logs

```bash
curl http://localhost:9090/audit/activity?limit=20 | jq
```

---

## Troubleshooting

### "Connection Refused" to localhost:9090

**Solution:**

```bash
# Check if AgentHub is running
lsof -i :9090

# Start AgentHub
launchctl start com.agenthub.router

# Or manually
cd ~/.local/share/agenthub
uvicorn router.main:app --port 9090
```

### "MCP Server Not Found"

**Solution:**

```bash
# List available servers
curl http://localhost:9090/servers | jq '.[] | .name'

# Check specific server status
curl http://localhost:9090/servers/context7 | jq '.status'

# Restart if needed
curl -X POST http://localhost:9090/servers/context7/restart
```

### "Ollama Connection Failed"

**Solution:**

```bash
# Check Ollama is running
ollama list

# Start Ollama
ollama serve

# Pull required models
ollama pull deepseek-r1:latest
ollama pull qwen3-coder:latest
```

### "Permission Denied" Errors

**Solution:**
- Grant Full Disk Access to your apps (System Settings → Privacy & Security)
- Apps needing access: Claude Desktop, VS Code, Raycast

---

## Getting Help

### Documentation

- **Build Spec**: `docs/build/BUILD-SPEC.md` - Architecture details
- **API Reference**: `docs/API.md` - Endpoint documentation
- **Audit System**: `docs/audit/` - Logging and compliance

### Dashboard

View real-time status: `http://localhost:9090/dashboard`

- Health monitoring
- Cache statistics
- Activity logs
- MCP server status

### Logs

```bash
# Router logs
tail -f ~/.local/share/agenthub/logs/router.log

# Audit logs
sqlite3 ~/.local/share/agenthub/audit.db "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10"

# Activity logs
sqlite3 ~/.local/share/agenthub/activity.db "SELECT * FROM activity ORDER BY timestamp DESC LIMIT 10"
```

---

## Next Steps

1. **Complete Setup**
   - [ ] Install AgentHub ([getting-started.md](getting-started.md))
   - [ ] Configure LaunchAgent ([launchagent-setup.md](launchagent-setup.md))
   - [ ] Set up credentials ([keychain-setup.md](keychain-setup.md))

2. **Integrate Clients**
   - [ ] Claude Desktop ([claude-desktop-integration.md](claude-desktop-integration.md))
   - [ ] VS Code ([vscode-integration.md](vscode-integration.md))
   - [ ] Raycast ([raycast-integration.md](raycast-integration.md))

3. **Test Everything**
   - [ ] Run test suite ([testing-integrations.md](testing-integrations.md))
   - [ ] Verify all 7 MCP servers work
   - [ ] Check prompt enhancement
   - [ ] Confirm caching works

4. **Explore Advanced Features**
   - [ ] Figma integration ([figma-integration.md](figma-integration.md))
   - [ ] ComfyUI workflows ([comfyui-integration.md](comfyui-integration.md))
   - [ ] Custom MCP servers
   - [ ] Monitoring & dashboards

---

## Contribute

Found an issue or have a suggestion? Check the project repository for contribution guidelines.
