# PromptHub — Project Rules for Continue

> This file is loaded into every Continue prompt. It is the primary source of project context.
> AGENTS.md is loaded separately and covers multi-agent workflow rules.

## Project Overview

PromptHub is a **local-first AI gateway for macOS** — a single router (`localhost:9090`) that manages MCP servers, enhances prompts via Ollama, and provides resilience patterns. All traffic stays on the local machine.

**Stack**: Python 3.11+, FastAPI 0.109+, httpx (async), Pydantic 2.5+, Jinja2, SQLite (aiosqlite), structlog, macOS Keychain (keyring)

**Node.js layer**: MCP bridge servers in `mcps/` (Node 20+, npm)

## Workspace Structure

```
prompthub/                        # Workspace root (opened in VS Code)
├── app/                          # Python project (FastAPI router)
│   ├── router/                   # FastAPI application package
│   │   ├── main.py               # Entry point, lifespan, ~30 endpoints
│   │   ├── config/               # Pydantic Settings, JSON config loading
│   │   ├── servers/              # MCP server lifecycle (bridge, process, registry, supervisor)
│   │   ├── resilience/           # Circuit breaker (CLOSED → OPEN → HALF_OPEN)
│   │   ├── cache/                # L1 in-memory LRU cache
│   │   ├── enhancement/          # Ollama HTTP clients, per-client prompt enhancement
│   │   ├── openai_compat/        # /v1/ proxy endpoints (chat completions, bearer auth)
│   │   ├── dashboard/            # HTMX observability UI (factory router)
│   │   ├── middleware/           # Audit context propagation, activity logging
│   │   ├── pipelines/            # Documentation generation workflow
│   │   ├── clients/              # Config generators (Claude Desktop, VS Code, Raycast)
│   │   ├── audit.py              # Structured JSON audit logging
│   │   ├── security_alerts.py    # Real-time anomaly detection
│   │   ├── audit_integrity.py    # SHA256 tamper detection
│   │   └── keyring_manager.py    # macOS Keychain integration
│   ├── configs/                  # Runtime JSON configs
│   │   ├── mcp-servers.json      # MCP server registry
│   │   ├── enhancement-rules.json # Per-client Ollama model + system prompt
│   │   └── api-keys.json         # Bearer tokens for /v1/ proxy
│   ├── tests/                    # Pytest suite (14 test files)
│   ├── templates/                # Jinja2 templates (dashboard)
│   ├── scripts/                  # Shell scripts
│   ├── docs/                     # Developer documentation
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .env                      # Environment config (Pydantic reads this)
├── clients/                      # Client setup (Claude Desktop, VS Code, Raycast, Cursor)
├── mcps/                         # Node.js MCP servers + unified bridge
│   ├── prompthub-bridge.js       # Stdio bridge aggregating all servers
│   └── package.json              # npm dependencies
├── .claude/steering/             # AI agent steering docs (product, tech, structure)
├── CLAUDE.md                     # Claude Code instructions
├── AGENTS.md                     # Multi-agent workflow rules (loaded separately)
├── README.md                     # Project overview
└── CHANGELOG.md                  # Version history
```

## Development Commands

All commands run from the `app/` directory:

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run router
uvicorn router.main:app --reload --port 9090

# Tests
pytest tests/ -v

# Linting & formatting
ruff check router/ && ruff format router/

# Type checking
mypy router/

# Health check
curl http://localhost:9090/health
```

## Module Architecture

This is a **modular monolith**. The main package is `app/router/`:

| Module | Purpose | Depends On |
|--------|---------|------------|
| `config/` | Pydantic Settings, env loading, JSON config | — |
| `servers/` | MCP server lifecycle: spawn, bridge, registry, supervisor | config/ |
| `resilience/` | Circuit breaker state machine (per-server isolation) | — |
| `cache/` | SHA256-keyed LRU cache with hit/miss tracking | — |
| `enhancement/` | Ollama HTTP clients, per-client model routing | cache/, resilience/ |
| `openai_compat/` | Bearer auth, SSE streaming, /v1 endpoints | enhancement/, resilience/ |
| `dashboard/` | HTMX templates, real-time partials | servers/, cache/, enhancement/ |
| `middleware/` | Audit context propagation (contextvars), activity logging | — |
| `pipelines/` | Multi-step documentation workflow | enhancement/, servers/ |
| `clients/` | Config generators for desktop apps | config/, servers/ |

### Factory Router Pattern

Dashboard and OpenAI proxy use factory functions that receive dependencies as arguments:

```python
def create_dashboard_router(
    get_servers: Callable, get_cache: Callable
) -> APIRouter:
    router = APIRouter(prefix="/dashboard")
    # endpoints are closures over dependencies
    return router
```

## API Endpoints

```
GET  /health                    Health check
GET  /servers                   List all MCP servers with status
POST /servers/{name}/start      Start a specific MCP server
POST /servers/{name}/stop       Stop a specific MCP server
POST /mcp/{server}/{path}       Proxy JSON-RPC to MCP server
POST /v1/chat/completions       OpenAI-compatible proxy (bearer auth required)
POST /v1/models                 List available models
POST /ollama/enhance            Enhance prompt via Ollama (X-Client-Name header)
GET  /dashboard                 HTMX monitoring dashboard
GET  /audit/activity            Query activity log (SQLite-backed)
POST /pipelines/documentation   Generate docs from codebase
```

## Request Flows

### MCP Proxy (`POST /mcp/{server}/{path}`)

```
Request → Circuit breaker check (reject if OPEN)
       → Auto-start server if configured (auto_start: true)
       → JSON-RPC proxied via stdio bridge to MCP server
       → Success/failure updates circuit breaker state
```

### OpenAI Proxy (`POST /v1/chat/completions`)

```
Request with Authorization: Bearer sk-prompthub-<client>-dev001
       → Token lookup in api-keys.json → resolve client_name + enhance flag
       → Circuit breaker check (ollama-proxy)
       → If enhance: true → last user message rewritten via Ollama
         (per-client model from enhancement-rules.json)
       → If enhance: false → pass through unchanged
       → Forward to Ollama (localhost:11434/v1/chat/completions)
       → Stream SSE or return JSON
```

### Direct Enhancement (`POST /ollama/enhance`)

```
Request with X-Client-Name header
       → Determines Ollama model from enhancement-rules.json
       → Cache check (SHA256 of prompt)
       → Ollama request with per-client system prompt
       → Cache result and return
```

## Configuration Files

### `app/.env` — Router Settings

```bash
HOST=127.0.0.1
PORT=9090
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=deepseek-r1:latest
OLLAMA_TIMEOUT=30
OLLAMA_API_MODE=native          # "native" (/api/generate) or "openai" (/v1/chat/completions)
CB_FAILURE_THRESHOLD=3          # Failures before circuit opens
CB_RECOVERY_TIMEOUT=30          # Seconds before half-open retry
CACHE_MAX_SIZE=1000             # LRU cache entries
API_KEYS_CONFIG="configs/api-keys.json"
ENHANCEMENT_RULES_CONFIG="configs/enhancement-rules.json"
MCP_SERVERS_CONFIG="configs/mcp-servers.json"
```

All settings use Pydantic `BaseSettings` with `SettingsConfigDict(env_file=".env")`.

### `app/configs/api-keys.json` — Bearer Tokens

Controls authentication for the `/v1/` proxy. Each token maps to a client and an enhancement flag:

```json
{
  "keys": {
    "sk-prompthub-continue-dev001": {
      "client_name": "continue",
      "enhance": false,
      "description": "Continue.dev extension (pass-through)"
    }
  }
}
```

- `enhance: true` → last user message rewritten by Ollama before forwarding
- `enhance: false` → transparent proxy (critical for IDE agents that send structured prompts)

### `app/configs/enhancement-rules.json` — Per-Client Models

```json
{
  "default": { "model": "deepseek-r1:latest", "system_prompt": "..." },
  "clients": {
    "claude-desktop": { "model": "deepseek-r1:latest" },
    "vscode":         { "model": "qwen2.5-coder:32b" },
    "claude-code":    { "model": "qwen2.5-coder:32b" },
    "cursor":         { "model": "deepseek-r1:latest" },
    "raycast":        { "model": "llama3.2:latest" },
    "obsidian":       { "model": "llama3.2:latest" }
  },
  "fallback_chain": ["llama3.2:latest", null]
}
```

### `app/configs/mcp-servers.json` — Server Registry

Defines 7 MCP servers: context7, desktop-commander, sequential-thinking, memory, deepseek-reasoner, obsidian, duckduckgo. Each server has:
- `command` + `args`: How to spawn the process
- `transport`: Always "stdio" (JSON-RPC over stdin/stdout)
- `auto_start`: Whether to start on first request
- `restart_on_failure` + `max_restarts`: Auto-recovery settings

## Key Patterns

### Circuit Breaker
```
CLOSED (normal) → 3 failures → OPEN (reject all) → 30s → HALF_OPEN (test one) → success → CLOSED
```
Each MCP server and the Ollama proxy have independent circuit breakers.

### Enhancement Pipeline
The enhancement service rewrites the **last user message** before forwarding. This improves freeform chat but **corrupts structured prompts** from IDE extensions. Always use `enhance: false` for agent/copilot tokens.

### Audit Events
```python
from router.audit import audit_admin_action, audit_credential_access

audit_admin_action(action="start", server_name="fetch", status="success")
audit_credential_access(action="get", credential_key="api_key", status="success")
```

Context is auto-captured via middleware `contextvars`: `request_id`, `client_id`, `client_ip`.

### Security Alerts
Real-time anomaly detection: repeated failures (3+ in 5 min), excessive credential access (5+ in 1 min), credential probing, configuration changes.

### Stdio Bridges
MCP servers communicate via JSON-RPC over stdin/stdout. The `prompthub-bridge.js` in `mcps/` aggregates all servers into a single stdio interface for Claude Desktop.

### Pydantic Settings
All configuration flows through the `Settings` class. Never hardcode values:
```python
from router.config.settings import Settings
settings = Settings()  # reads .env automatically
```

## Code Style

- Python 3.11+ features (union types `X | None`, match statements)
- Type hints required on all public functions
- 88-char line limit (ruff format)
- Use `logging` module, never `print()`
- Async everywhere: `httpx` for HTTP, `asyncio` for I/O — never `requests`
- No global state; use dependency injection via FastAPI
- Imports sorted by isort (via ruff)

## File Naming Conventions

| Category | Pattern | Example |
|----------|---------|---------|
| ADRs | `ADR-NNN-decision-name.md` | `ADR-001-stdio-transport.md` |
| Feature docs | `FEATURE-NAME-COMPLETE.md` | `OPENAI-PROXY-COMPLETE.md` |
| Config files | kebab-case `.json` | `mcp-servers.json` |
| Python modules | snake_case `.py` | `keyring_manager.py` |
| Test files | `test_module.py` | `test_openai_compat.py` |

## Documentation Locations

| Content | Location | Audience |
|---------|----------|----------|
| User guides | `~/Vault/PromptHub/` (Obsidian) | End users |
| Developer docs | `app/docs/` | Developers |
| API spec | `app/docs/api/openapi.yaml` | Developers |
| Agent steering | `.claude/steering/` | AI agents |
| Project metadata | `CLAUDE.md`, `AGENTS.md`, `CHANGELOG.md` | AI agents |

## Business Rules

- Enhancement failures are **non-fatal** — the original prompt is always forwarded
- All security-relevant operations produce audit events
- Credentials are stored in macOS Keychain via `keyring`, never in plaintext
- The router is **local-only** (`127.0.0.1`); no public-facing deployment
- API keys follow the `sk-prompthub-{client}-dev001` convention

## When Editing This Project

1. Run `ruff check router/ && ruff format router/` after changing Python files
2. Run `pytest tests/ -v` to verify nothing is broken
3. Configuration lives in `app/configs/` JSON files, not in code
4. Use `audit_event()` or convenience wrappers when adding security-relevant operations
5. Follow the factory router pattern for new endpoint groups
6. Cross-directory paths (e.g., mcps/) must use `Settings.workspace_root`
