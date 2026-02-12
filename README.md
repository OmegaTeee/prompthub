# AgentHub

Lightweight local-first AI agent hub for macOS — central router, prompt enhancement, and desktop integrations.

## Overview

AgentHub provides a single local router (`localhost:9090`) that:
- Manages MCP servers centrally (configure once, use everywhere)
- Enhances prompts via Ollama before forwarding to AI services
- Provides circuit breakers for graceful degradation
- Caches responses for performance

**Target clients**: Claude Desktop, VS Code, Raycast, Obsidian, ComfyUI

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 2 | **Complete** | Core router, caching, circuit breakers, Ollama enhancement |
| Phase 2.5 | **Complete** | MCP server management, stdio bridges |
| Phase 3 | **Complete** | Desktop integration, config generators, documentation pipeline |
| Phase 4 | **Complete** | HTMX dashboard with real-time monitoring |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+ (for MCP servers)
- Docker Desktop or Colima
- Ollama running locally (`ollama serve`)

### Development

```bash
# Create virtual environment (from app/ directory)
cd app
python -m venv .venv && source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install MCP servers (Node.js packages)
cd ../mcps && npm install && cd ..

# Run router
cd app && uvicorn router.main:app --reload --port 9090

# Verify health
curl http://localhost:9090/health
```

### Docker

```bash
cd app && docker compose up -d
curl http://localhost:9090/health
```

## Project Structure

```
agenthub/
├── app/                    # Python FastAPI project
│   ├── router/             # FastAPI application
│   ├── tests/              # Pytest test suite
│   ├── configs/            # Runtime configuration
│   │   ├── mcp-servers.json    # MCP server registry
│   │   └── enhancement-rules.json
│   ├── templates/          # Jinja2 templates for dashboard
│   ├── scripts/            # Shell wrapper scripts
│   ├── docs/               # Developer documentation
│   ├── Dockerfile
│   └── pyproject.toml
├── clients/                # Client setup configs and scripts
│   ├── claude/             # Claude Desktop configuration
│   ├── vscode/             # VS Code configuration
│   ├── raycast/            # Raycast configuration
│   └── launch_agents/      # macOS LaunchAgent plists
├── guides/                 # User guides (Obsidian vault)
├── mcps/                   # Centralized MCP servers (Node.js)
│   ├── package.json        # npm dependencies for MCP servers
│   └── obsidian-mcp-tools/ # Obsidian vault integration
└── mcp-agenthub.code-workspace
```

## Documentation

### User Guides
See **[guides/](guides/)** for user-facing documentation:
- [Getting Started](guides/getting-started.md) - Quick start and verification
- [Keychain Setup](guides/keychain-setup.md) - Secure credential storage
- [LaunchAgent Setup](guides/launchagent-setup.md) - Background service setup
- [App Configs](guides/app-configs.md) - Claude Desktop, VS Code, Raycast, Obsidian
- [Figma Integration](guides/figma-integration.md) - Design-to-code workflows
- [ComfyUI Integration](guides/comfyui-integration.md) - Image generation workflows

### Client Setup
See **[clients/](clients/)** for client-specific configurations:
- [Claude Desktop](clients/claude/) - Config files and setup script
- [VS Code](clients/vscode/) - Settings and tasks config
- [Raycast](clients/raycast/) - MCP server config

### Developer Documentation
See **[app/docs/](app/docs/)** for technical documentation:
- [Audit System](app/docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md) - Production audit infrastructure (Security Score: 9.0/10)

## Key Features

### Prompt Enhancement
Each client (Claude, VS Code, Raycast) gets customized prompt enhancement:
- **Claude Desktop**: deepseek-r1 for structured reasoning
- **VS Code / Claude Code**: qwen3-coder for code-focused responses
- **Raycast**: deepseek-r1 for action-oriented responses
- **Obsidian**: deepseek-r1 with Markdown formatting

### Circuit Breakers
If an MCP server fails:
1. Circuit opens after 3 consecutive failures
2. Requests return fallback immediately (no hanging)
3. Circuit tests recovery after 30 seconds
4. Automatic restoration when service recovers

### Caching
- **L1**: Exact match (SHA256 hash) - instant response
- **L2**: Semantic similarity (Phase 2.1) - similar prompts hit cache

## Dashboard

Access the monitoring dashboard at:

```
http://localhost:9090/dashboard
```

Features:
- Service health status (auto-refresh every 5s)
- Cache stats and Ollama status (auto-refresh every 10s)
- Recent request activity (auto-refresh every 3s)
- Quick actions: clear cache, restart servers

## MCP Servers

AgentHub manages 7 MCP servers:

| Server | Package | Auto-Start | Description |
|--------|---------|------------|-------------|
| context7 | @upstash/context7-mcp | Yes | Documentation fetching |
| desktop-commander | @wonderwhy-er/desktop-commander | Yes | File operations |
| sequential-thinking | @modelcontextprotocol/server-sequential-thinking | Yes | Step-by-step reasoning |
| obsidian | obsidian-mcp-tools | Yes | Semantic search, templates for Obsidian vault |
| memory | @modelcontextprotocol/server-memory | No | Cross-session persistence |
| deepseek-reasoner | deepseek-reasoner-mcp | No | Local reasoning |
| fetch | mcp-fetch | No | HTTP fetch, GraphQL |

> See [app/configs/mcp-servers.json.examples](app/configs/mcp-servers.json.examples) for additional server examples including Python-based MCPs.

### Adding/Updating MCPs

**For npm packages:**

```bash
cd mcps
npm install <package-name>
# Update app/configs/mcp-servers.json with the new server
```

**For standalone binaries (like obsidian-mcp-tools):**

```bash
# Create directory
mkdir -p mcps/<mcp-name>/bin

# Copy binary
cp /path/to/binary mcps/<mcp-name>/bin/

# Create wrapper script (if API keys needed)
# See app/scripts/README.md for wrapper pattern
```

**For Python packages:**

```bash
# Add to app/requirements.txt
echo "<package-name>" >> app/requirements.txt

# Install in virtual environment
cd app && source .venv/bin/activate
pip install -r requirements.txt

# Create wrapper script (if API keys needed)
# See mcps/obsidian-mcp-tools/PYTHON-MCP-EXAMPLE.md for complete pattern
```

### API Key Management

MCP servers requiring API keys use wrapper scripts that retrieve credentials from macOS Keychain. See [app/scripts/README.md](app/scripts/README.md) for details.

**Add API keys to Keychain:**

```bash
security add-generic-password -a $USER -s obsidian_api_key -w YOUR_API_KEY
```

**Validate installation:**

```bash
./app/scripts/router/validate-mcp-servers.sh
```

## Configuration

### Environment Variables
Copy `app/.env.example` to `app/.env` and configure:

```bash
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
ROUTER_PORT=9090
```

### MCP Servers
Edit `app/configs/mcp-servers.json` to add/remove MCP servers.

### Enhancement Rules
Edit `app/configs/enhancement-rules.json` to customize per-client behavior.

## API Reference

AgentHub provides REST APIs for MCP server management, prompt enhancement, and monitoring.

### Base URL

```
http://localhost:9090
```

### Core Endpoints

#### Health & Status

```bash
# System health check
GET /health

# Specific server health
GET /health/{server}
```

**Example Response:**

```json
{
  "status": "healthy",
  "services": {
    "router": "up",
    "ollama": "up",
    "cache": {"status": "up", "hit_rate": 0.82, "size": 145}
  },
  "servers": {
    "running": 5,
    "stopped": 2,
    "failed": 0
  }
}
```

#### Server Management

```bash
# List all MCP servers
GET /servers

# Get server details
GET /servers/{name}

# Start/stop/restart server
POST /servers/{name}/start
POST /servers/{name}/stop
POST /servers/{name}/restart

# Install new MCP server
POST /servers/install
{
  "package": "@upstash/context7-mcp",
  "name": "context7",
  "auto_start": true,
  "description": "Documentation fetching"
}

# Remove server
DELETE /servers/{name}
```

#### MCP Proxy

```bash
# Proxy JSON-RPC to MCP server
POST /mcp/{server}/{path}
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {"name": "fetch_docs", "arguments": {"library": "fastapi"}},
  "id": 1
}
```

**Example - Fetch docs via context7:**

```bash
curl -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "query-docs",
      "arguments": {"library": "fastapi", "query": "authentication"}
    },
    "id": 1
  }'
```

#### Prompt Enhancement

```bash
# Enhance prompt with Ollama
POST /ollama/enhance
{
  "prompt": "Explain JWT authentication",
  "bypass_cache": false
}

# Headers:
X-Client-Name: claude-desktop  # Routes to deepseek-r1
X-Client-Name: vscode          # Routes to qwen3-coder
X-Client-Name: raycast         # Routes to deepseek-r1
X-Client-Name: obsidian        # Routes to deepseek-r1 with markdown
```

**Example Response:**

```json
{
  "original": "Explain JWT authentication",
  "enhanced": "Provide a comprehensive explanation of JWT...",
  "model": "deepseek-r1:latest",
  "cached": false,
  "was_enhanced": true,
  "error": null
}
```

#### Circuit Breakers

```bash
# List all circuit breaker states
GET /circuit-breakers

# Reset circuit breaker
POST /circuit-breakers/{name}/reset
```

#### Audit & Activity

```bash
# Query activity log
GET /audit/activity?client_id=admin&limit=50

# Activity statistics
GET /audit/activity/stats

# Security alerts
GET /security/alerts?severity=critical

# Verify audit integrity
GET /audit/integrity/verify
```

#### Client Configurations

```bash
# Generate config for Claude Desktop
GET /configs/claude-desktop

# Generate config for VS Code
GET /configs/vscode

# Generate Raycast script
GET /configs/raycast
```

### Error Handling

All endpoints follow JSON-RPC error format:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Server fetch circuit breaker open",
    "data": {"retry_after": 30}
  },
  "id": null
}
```

**Common Error Codes:**
- `404` - Server/resource not found
- `400` - Invalid request (server already running, etc.)
- `503` - Service unavailable (circuit breaker open, service not initialized)
- `500` - Internal server error

### Rate Limiting & Caching

- **Cache TTL**: 2 hours (7200s)
- **Cache Strategy**: SHA256 hash-based exact match (L1), semantic similarity (L2, future)
- **Circuit Breaker**: 3 failures → OPEN (30s timeout) → HALF_OPEN → CLOSED

### Authentication

Currently no authentication required (local-only deployment). For production:
- Use API keys via `X-API-Key` header
- Configure in `.env`: `API_KEY_REQUIRED=true`
- See [guides/keychain-setup.md](guides/keychain-setup.md)

## Contributing

1. Read `CLAUDE.md` to understand the architecture
2. Run tests: `cd app && pytest tests/ -v`
3. Check types: `cd app && mypy router/`
4. Format code: `cd app && ruff format router/`
5. Submit PRs against `main`

### Code Style Guidelines
- Python 3.11+ with type hints (required)
- 88-char line limit (Black/ruff)
- Use `logging`, not `print()`
- Async everywhere (`httpx`, not `requests`)
- No global state; use dependency injection

## License

MIT License - See [LICENSE](LICENSE)
