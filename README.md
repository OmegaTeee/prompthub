# PromptHub

Lightweight local-first service orchestration layer for macOS — central router, prompt enhancement, and desktop integrations. See [docs/glossary.md](docs/glossary.md) for terminology.

## Overview

Service provides a single local router (`localhost:9090`) that:
- Manages MCP servers centrally (configure once, use everywhere)
- Enhances prompts via LM Studio before forwarding to AI services
- Provides circuit breakers for graceful degradation
- Caches responses for performance

**Target clients**: Claude Desktop, VS Code, Raycast, Obsidian, ComfyUI

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 2 | **Complete** | Core router, caching, circuit breakers, LM Studio enhancement |
| Phase 2.5 | **Complete** | MCP server management, stdio bridges |
| Phase 3 | **Complete** | Desktop integration, repo-managed client configs, documentation pipeline |
| Phase 4 | **Complete** | HTMX dashboard with real-time monitoring |
| Phase 5 | **Complete** | OpenAI-compatible API proxy for desktop apps |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+ (for MCP servers)
- Docker Desktop or Colima
- LM Studio running locally (`lms server start`)

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
prompthub/
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
├── mcps/                   # MCP servers (Node.js) + client configs
│   ├── prompthub-bridge.js # Stdio bridge aggregating all servers
│   ├── configs/            # Desktop client configs (Claude, Raycast, Inspector)
│   ├── package.json        # npm dependencies for MCP servers
│   └── obsidian-mcp-tools/ # Obsidian vault integration
└── .claude/steering/       # AI agent steering documents
```

## Documentation

### User Guides
User-facing guides live in [`docs/guides/`](docs/guides/):
- [Quick Start](docs/guides/01-quick-start-guide.md)
- [Prompt Enhancement](docs/guides/02-prompt-enhancement-user-guide.md)
- [Session Memory](docs/guides/03-session-memory-guide.md)
- [OpenAI-Compatible API](docs/guides/04-openai-api-guide.md)
- [Client Configuration](docs/guides/06-client-configuration-guide.md)

### Client Setup
Client setup now lives under [`clients/`](clients/):
- [Claude](clients/claude/) - Claude app configs and setup helpers
- [Raycast](clients/raycast/) - MCP and provider configuration
- [VS Code](clients/vscode/) - MCP and editor integration files
- [LM Studio](clients/lm-studio/) - local model presets and setup notes

### Developer Documentation
See **[docs/](docs/)** for technical documentation:
- [Audit System](docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md) - Production audit infrastructure (Security Score: 9.0/10)

## Key Features

### Prompt Enhancement

Prompts pass through a local LM Studio model before reaching the AI service. Each client gets a tailored system prompt, privacy policy, and enhancement settings:

| Client | Default model | Tuning |
|--------|---------------|--------|
| Claude Desktop | qwen3-4b-instruct-2507 | Structured reasoning, Markdown |
| VS Code / Claude Code | qwen3-4b-instruct-2507 | Code-first, file paths, minimal prose |
| Raycast | qwen3-4b-instruct-2507 | Action-oriented, CLI commands, under 200 words |
| Obsidian | qwen3-4b-instruct-2507 | Markdown with `[[wikilinks]]` and `#tags` |

Enhancement is optional per-client and fails gracefully — if LM Studio is unreachable, the original prompt passes through unchanged. Configure models and system prompts in `app/configs/enhancement-rules.json`.

### OpenAI-Compatible API Proxy

Any app that speaks the OpenAI API can connect to local LM Studio models through PromptHub's `/v1/` endpoints. Supports `POST /v1/chat/completions` (streaming and non-streaming) and `GET /v1/models`. Authenticated via bearer tokens, with optional prompt enhancement applied before forwarding.

Use this to connect VS Code chat, Cursor, Raycast AI, or any OpenAI-compatible client to local models without changing their configuration beyond the base URL and API key.

### Circuit Breakers

Every MCP server and the LM Studio service is wrapped in a circuit breaker. When a service fails 3 times, the circuit opens and requests return immediately with a fallback — no hanging, no timeouts piling up. After 30 seconds, one test request probes recovery. On success, full traffic resumes automatically.

Monitor and reset breakers via `GET /circuit-breakers` and `POST /circuit-breakers/{name}/reset`.

### Caching

Enhanced prompts are cached in an in-memory LRU store (up to 1,000 entries, 1-hour TTL). Cache keys are SHA-256 hashes of the prompt content, providing exact-match deduplication. Repeated identical prompts return instantly without hitting LM Studio.

### Dashboard

HTMX-powered monitoring UI at `localhost:9090/dashboard` with auto-refreshing panels for service health (5s), cache and LM Studio status (10s), and request activity (3s). Includes quick actions to clear cache and restart individual MCP servers.

## MCP Servers

PromptHub manages 6 MCP servers:

| Server | Package | Auto-Start | Description |
|--------|---------|------------|-------------|
| context7 | @upstash/context7-mcp | Yes | Documentation fetching |
| desktop-commander | @wonderwhy-er/desktop-commander | Yes | File operations |
| sequential-thinking | @modelcontextprotocol/server-sequential-thinking | Yes | Step-by-step reasoning |
| obsidian | obsidian-mcp-tools | Yes | Semantic search, templates for Obsidian vault |
| memory | @modelcontextprotocol/server-memory | No | Cross-session persistence |
| fetch | mcp-fetch | No | HTTP fetch, GraphQL |

> See [`app/configs/mcp-servers.json`](./app/configs/mcp-servers.json) for the
> active registry and [`mcps/README.md`](./mcps/README.md) for server-specific
> notes.

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
# See scripts/README.md for wrapper pattern
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

MCP servers requiring API keys use wrapper scripts that retrieve credentials from macOS Keychain. See [scripts/README.md](scripts/README.md) for details.

**Add API keys to Keychain:**

```bash
security add-generic-password -a $USER -s obsidian_api_key -w YOUR_API_KEY
```

**Validate installation:**

```bash
./scripts/router/validate-mcp-servers.sh
```

## Configuration

### Environment Variables
Copy `app/.env.example` to `app/.env` and configure:

```bash
LM_STUDIO_HOST=host.docker.internal
LM_STUDIO_PORT=1234
ROUTER_PORT=9090
```

### MCP Servers
Edit `app/configs/mcp-servers.json` to add/remove MCP servers.

### Enhancement Rules
Edit `app/configs/enhancement-rules.json` to customize per-client behavior.

## API Reference

PromptHub provides REST APIs for MCP server management, prompt enhancement, and monitoring.

Full OpenAPI 3.0 specification: **[docs/api/openapi.yaml](docs/api/openapi.yaml)** (43 endpoints)

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
    "lm_studio": "up",
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
# Enhance prompt with LM Studio
POST /llm/enhance
{
  "prompt": "Explain JWT authentication",
  "bypass_cache": false
}

# Headers:
X-Client-Name: claude-desktop  # Routes to qwen3-4b-instruct-2507
X-Client-Name: vscode          # Routes to qwen3-4b-instruct-2507
X-Client-Name: raycast         # Routes to qwen3-4b-instruct-2507
X-Client-Name: obsidian        # Routes to qwen3-4b-instruct-2507 with markdown
```

**Example Response:**

```json
{
  "original": "Explain JWT authentication",
  "enhanced": "Provide a comprehensive explanation of JWT...",
  "model": "qwen3-4b-instruct-2507",
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

#### Client Configuration Sources

```bash
# Client configs are stored as files in the repo, not generated over HTTP
clients/claude/
clients/vscode/
clients/raycast/
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
- See Obsidian vault: `~/Vault/PromptHub/Core Setup/Keychain.md`

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
