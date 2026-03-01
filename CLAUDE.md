# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PromptHub is a centralized MCP (Model Context Protocol) router for macOS. It provides a single local endpoint (`localhost:9090`) that manages MCP servers, enhances prompts via Ollama, and provides resilience patterns.

## Workspace Structure

This is a **multi-root workspace** with clear separation between the Python project, client configs, user guides, and MCP servers:

```
prompthub/                        # Workspace root
├── app/                          # Python project (FastAPI router + CLI)
│   ├── router/                   # FastAPI application
│   ├── cli/                      # MCP Config Manager (Typer CLI)
│   ├── tests/                    # Pytest suite
│   ├── configs/                  # Runtime configs (mcp-servers.json, api-keys.json, etc.)
│   ├── templates/                # Jinja2 + HTMX templates (dashboard, partials)
│   ├── scripts/                  # Shell scripts and LaunchAgent plist
│   ├── docs/                     # Developer/engineering docs and ADRs
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
├── mcps/                         # MCP servers (Node.js bridge) + client configs
│   ├── prompthub-bridge.js       # Stdio bridge aggregating all servers
│   ├── configs/                  # Desktop client configs (Claude, Raycast, Inspector)
│   └── package.json              # npm dependencies
├── logs/                         # LaunchAgent stdout/stderr logs
└── .claude/ .github/ .vscode/    # Workspace-level configs
# User guides live in Obsidian vault: ~/Vault/PromptHub/
```

## Development Commands

```bash
# Setup
cd app && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run router (from app/ directory)
cd app && uvicorn router.main:app --reload --port 9090

# Run tests
cd app && pytest tests/ -v

# Type checking
cd app && mypy router/

# Linting (ruff)
cd app && ruff check router/
cd app && ruff format router/

# Verify health
curl http://localhost:9090/health

# MCP Config Manager CLI (from app/ directory)
cd app && python -m cli generate claude-desktop    # Print bridge config JSON
cd app && python -m cli validate claude-desktop    # Check installed config
cd app && python -m cli diagnose                   # Full stack health check
cd app && python -m cli list                       # Show all clients + paths

# LaunchAgent (production daemon)
launchctl kickstart -k gui/$(id -u)/com.prompthub.router
tail -f logs/router-stderr.log
```

## Architecture

This is a **modular monolith** built with FastAPI. The main package is `app/router/` with these modules:

| Module               | Purpose                                                                                                           |
| -------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `routes/`            | Route handlers extracted from main.py (health, servers, mcp_proxy, enhancement, audit, pipelines, client_configs) |
| `config/`            | Pydantic settings, JSON config loading                                                                            |
| `servers/`           | MCP server lifecycle via FastMCP (spawn, monitor, restart stdio processes)                                        |
| `resilience/`        | Circuit breaker (CLOSED → OPEN → HALF_OPEN states)                                                                |
| `cache/`             | L1 in-memory LRU + L2 SQLite persistent write-through cache                                                       |
| `enhancement/`       | Ollama HTTP client (native + OpenAI-compat), per-client prompt enhancement, cloud fallback via OpenRouter, token budget truncation |
| `orchestrator/`      | Pre-enhancement intent classifier (qwen3:14b) — classifies prompts, suggests tools, annotates for enhancement     |
| `openai_compat/`     | OpenAI-compatible `/v1/` proxy with bearer auth and optional enhancement                                          |
| `memory/`            | Session memory and context management (SQLite-backed facts, memory blocks, MCP sync)                              |
| `tool_registry/`     | MCP tool definition cache (SQLite-backed snapshots, automatic archival, cache-through proxy)                      |
| `dashboard/`         | HTMX observability UI (servers, cache, circuit breakers, Ollama, memory, tool registry panels)                    |
| `pipelines/`         | Workflow orchestration (documentation generation)                                                                 |
| `clients/`           | Config generators for desktop apps (delegates to `cli/` for bridge configs)                                       |
| `cli/`               | MCP Config Manager CLI — generate, install, validate, diff, list, diagnose (Typer)                                |
| `middleware/`        | Audit context, activity logging, request timeout, persistent storage                                              |
| `audit.py`           | Structured audit logging with security alerts                                                                     |
| `security_alerts.py` | Real-time anomaly detection and alerting                                                                          |
| `audit_integrity.py` | Tamper detection with SHA256 checksums                                                                            |
| `keyring_manager.py` | Credential management with macOS Keychain                                                                         |

### Request Flow

1. Request arrives at `/mcp/{server}/{path}`
2. Circuit breaker checked (reject if OPEN)
3. For `tools/list`: check tool registry cache → return if hit
4. Server auto-started if configured with `auto_start: true`
5. JSON-RPC proxied via FastMCP bridge (StdioTransport)
6. For `tools/list`: cache raw response in tool registry (SQLite)
7. Success/failure updates circuit breaker state

### Key Patterns

- **Pydantic Settings**: All config via `BaseSettings` with `.env` support
- **Async everywhere**: Use `httpx` (not `requests`), `asyncio` for I/O
- **Circuit breaker**: 3 failures → OPEN, 30s → HALF_OPEN, success → CLOSED
- **FastMCP bridges**: MCP servers communicate via FastMCP Client + StdioTransport
- **Factory-with-getter-callables**: Route modules use `create_X_router(get_service=lambda: service)` to defer global resolution past lifespan init
- **Tiered timeouts**: httpx client (120s) → middleware (60s default, 180s for slow paths) → Ollama keep_alive (5min)
- **Task-specific models**: Per-client enhancement models (gemma3:4b default, gemma3:27b for claude-desktop, qwen3-coder:30b for claude-code) with orchestrator agent (qwen3:14b) for intent classification (see ADR-008, supersedes ADR-006)
- **Privacy boundary**: `PrivacyLevel` enum (`local_only`, `free_ok`, `any`) controls whether prompts leave localhost (see ADR-007)
- **Cloud fallback**: When Ollama fails, `free_ok`/`any` clients fall back to OpenRouter free-tier; `local_only` never leaves localhost
- **Tool registry cache-through**: `tools/list` responses cached in SQLite (24h TTL), served from cache on subsequent requests; old snapshots archived automatically for long-term access
- **Schema minification**: Bridge strips verbose fields (`description`, `title`, `examples`, `default`) from tool `inputSchema` before sending to LLM clients, reducing context usage by ~67%
- **Token budget**: Enhancement input capped at 4,096 tokens via `TokenBudget` — truncates at word boundaries with notice; prevents wasting context on prompt rewrites

## Configuration Files

- `app/configs/mcp-servers.json` - MCP server registry (command, args, env, auto_start, restart_on_failure)
- `app/configs/enhancement-rules.json` - Per-client enhancement system prompts, privacy_level, model, temperature, max_tokens
- `app/configs/api-keys.json` - Bearer tokens for OpenAI-compatible proxy (client_name, enhance flag)
- `app/configs/cloud-models.json` - Cloud fallback model mapping (local models → free-tier cloud equivalents)
- `app/.env` - Runtime settings (OLLAMA_TIMEOUT=120, OPENROUTER_ENABLED, OPENROUTER_API_KEY, etc.)

## API Endpoints

```
GET  /health                    Health check
GET  /servers                   List all MCP servers
POST /servers/{name}/start      Start server
POST /servers/{name}/stop       Stop server
POST /mcp/{server}/{path}       Proxy JSON-RPC to MCP server
POST /mcp-direct/mcp            Streamable HTTP endpoint (FastMCP gateway)
POST /ollama/enhance            Enhance prompt via Ollama (X-Client-Name, X-Privacy-Level headers)
                                Response includes: provider ("ollama"|"openrouter"), privacy_level
POST /ollama/orchestrate        Classify intent and annotate prompt (qwen3:14b orchestrator)
POST /sessions                  Create session (memory system)
GET  /sessions/{id}/context     Full session context (facts + blocks + MCP graph)
GET  /dashboard                 HTMX monitoring dashboard (servers, cache, Ollama, memory panels)
POST /pipelines/documentation   Generate docs from codebase
POST /v1/chat/completions       OpenAI-compatible proxy → Ollama (bearer auth, optional enhancement)
GET  /v1/models                 List Ollama models (OpenAI format)
GET  /audit/activity            Query persistent activity log
GET  /security/alerts           Recent security alerts
GET  /tools                     List all cached tool snapshots (tool registry)
GET  /tools/{server}            Get raw cached tools for a server (pre-minification)
GET  /tools/stats               Tool registry statistics (cached servers, total tools, archive count)
POST /tools/{server}/refresh    Force re-fetch tools from live server
DEL  /tools/{server}            Clear cached tools for a server
POST /tools/archive             Archive expired tool cache entries
POST /tools/cleanup             Delete old archived snapshots (retention_days param)
GET  /configs/claude-desktop    Generate Claude Desktop bridge config
GET  /configs/vscode            Generate VS Code bridge config
GET  /configs/raycast           Generate Raycast bridge config
```

## Code Style

- Python 3.11+ features, type hints required
- 88-char line limit (Black/ruff format)
- Use `logging` module, not `print()`
- Avoid global state; use dependency injection
- Never hardcode config; use Settings class

## Audit & Security

**Security Score: 9.0/10** - Production-grade audit infrastructure with compliance-ready logging.

### Structured Audit Logging

All security-relevant operations are logged with structured JSON:

```python
from router.audit import audit_admin_action, audit_credential_access

# Dashboard actions
audit_admin_action(action="start", server_name="fetch", status="success")

# Credential access
audit_credential_access(action="get", credential_key="api_key", status="success")
```

### Audit Context Propagation

Context is automatically captured via middleware using `contextvars`:

- `request_id` - UUID for request correlation
- `client_id` - From X-Client-ID header
- `client_ip` - Remote IP address (respects X-Forwarded-For)

### Security Alerts

Real-time anomaly detection integrated into audit events:

- Repeated failures (3+ in 5 min)
- Excessive credential access (5+ in 1 min)
- Credential probing attempts
- Configuration changes

Alerts are automatically checked on every audit event.

### Persistent Activity Log

SQLite-backed activity log stores HTTP request history with full audit context.
Query API: `GET /audit/activity?client_id=admin&limit=50`

### Documentation

- **User Guides**: Obsidian vault (`~/Vault/PromptHub/`) - Setup, configuration, integrations
- **Developer Docs**: `app/docs/` - Architecture, audit system, security
- **Audit Implementation**: `app/docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md`

For detailed audit system documentation, see `app/docs/audit/`

## Steering Documents

Steering documents guide AI agents with project-specific conventions and patterns. These documents are located in `.claude/steering/`:

| Document         | Purpose                                                                             | Path                            |
| ---------------- | ----------------------------------------------------------------------------------- | ------------------------------- |
| **product.md**   | Product purpose, value proposition, key features, business rules, request lifecycle | `.claude/steering/product.md`   |
| **tech.md**      | Tech stack, frameworks, build system, common commands, code style requirements      | `.claude/steering/tech.md`      |
| **structure.md** | Directory organization, file naming patterns, module responsibilities, request flow | `.claude/steering/structure.md` |

## Available agents

- `code-docs`: Improve docstrings, comments, and type hints for existing code without changing behavior.
- `user-manual`: Generate user-facing documentation (Quickstart, Usage, Examples) based on the current codebase.

These documents provide focused guidance for AI agents working on this codebase and should be referenced during onboarding and complex tasks.
