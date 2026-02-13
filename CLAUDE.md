# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PromptHub is a centralized MCP (Model Context Protocol) router for macOS. It provides a single local endpoint (`localhost:9090`) that manages MCP servers, enhances prompts via Ollama, and provides resilience patterns.

## Workspace Structure

This is a **multi-root workspace** with clear separation between the Python project, client configs, user guides, and MCP servers:

```
prompthub/                        # Workspace root
├── app/                          # Python project (FastAPI router)
│   ├── router/                   # FastAPI application
│   ├── tests/                    # Pytest suite
│   ├── configs/                  # Runtime configs (mcp-servers.json, enhancement-rules.json)
│   ├── templates/                # Jinja2 templates
│   ├── scripts/                  # Shell scripts
│   ├── docs/                     # Developer/engineering documentation
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
├── clients/                      # Client setup (Claude Desktop, VS Code, Raycast, Cursor)
├── mcps/                         # Node.js MCP servers
└── .claude/ .github/ .vscode/    # Workspace-level configs
# User guides live in Obsidian vault: ~/Vault/PromptHub/
```

## Development Commands

```bash
# Setup
cd app && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../mcps && npm install && cd ..

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
```

## Architecture

This is a **modular monolith** built with FastAPI. The main package is `app/router/` with these modules:

| Module | Purpose |
|--------|---------|
| `config/` | Pydantic settings, JSON config loading |
| `servers/` | MCP server lifecycle (spawn, monitor, restart stdio processes) |
| `routing/` | MCP server registry, JSON-RPC proxy |
| `resilience/` | Circuit breaker (CLOSED → OPEN → HALF_OPEN states) |
| `cache/` | L1 in-memory LRU cache |
| `enhancement/` | Ollama HTTP client, per-client prompt enhancement |
| `dashboard/` | HTMX observability UI |
| `pipelines/` | Workflow orchestration (documentation generation) |
| `clients/` | Config generators for Claude Desktop, VS Code, Raycast |
| `middleware/` | Audit context, activity logging, persistent storage |
| `audit.py` | Structured audit logging with security alerts |
| `security_alerts.py` | Real-time anomaly detection and alerting |
| `audit_integrity.py` | Tamper detection with SHA256 checksums |
| `keyring_manager.py` | Credential management with macOS Keychain |

### Request Flow

1. Request arrives at `/mcp/{server}/{path}`
2. Circuit breaker checked (reject if OPEN)
3. Server auto-started if configured with `auto_start: true`
4. JSON-RPC proxied via stdio bridge
5. Success/failure updates circuit breaker state

### Key Patterns

- **Pydantic Settings**: All config via `BaseSettings` with `.env` support
- **Async everywhere**: Use `httpx` (not `requests`), `asyncio` for I/O
- **Circuit breaker**: 3 failures → OPEN, 30s → HALF_OPEN, success → CLOSED
- **Stdio bridges**: MCP servers communicate via JSON-RPC over stdin/stdout
- **workspace_root**: Cross-directory paths (mcps/) resolved via `Settings.workspace_root`

## Configuration Files

- `app/configs/mcp-servers.json` - MCP server registry (command, args, auto_start, restart_on_failure)
- `app/configs/enhancement-rules.json` - Per-client Ollama model selection and system prompts

## API Endpoints

```
GET  /health                    Health check
GET  /servers                   List all MCP servers
POST /servers/{name}/start      Start server
POST /servers/{name}/stop       Stop server
POST /mcp/{server}/{path}       Proxy JSON-RPC to MCP server
POST /ollama/enhance            Enhance prompt via Ollama (X-Client-Name header)
GET  /dashboard                 HTMX monitoring dashboard
POST /pipelines/documentation   Generate docs from codebase
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

| Document | Purpose | Path |
|----------|---------|------|
| **product.md** | Product purpose, value proposition, key features, business rules, request lifecycle | `.claude/steering/product.md` |
| **tech.md** | Tech stack, frameworks, build system, common commands, code style requirements | `.claude/steering/tech.md` |
| **structure.md** | Directory organization, file naming patterns, module responsibilities, request flow | `.claude/steering/structure.md` |

These documents provide focused guidance for AI agents working on this codebase and should be referenced during onboarding and complex tasks.
