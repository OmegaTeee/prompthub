# Product — PromptHub

## Purpose

PromptHub is a **local-first AI gateway for macOS** — a single router (`localhost:9090`) that unifies prompt routing, MCP servers, and desktop client integrations behind one endpoint.

## Value Proposition

- **Configure once, use everywhere** — MCP servers are managed centrally; clients (Claude Desktop, VS Code, Cursor, Raycast, Obsidian) all connect to one router
- **Invisible enhancement** — Prompts are automatically improved via Ollama using per-client models before reaching the AI service
- **Resilience built-in** — Circuit breakers, auto-restart, caching prevent cascading failures
- **Observable** — Dashboard, audit logging, security alerts give full visibility into what's happening

## Target Users

macOS power users who work across multiple AI-powered editors and tools and want a stable, observable control plane for local and remote models.

## Key Features

| Feature | Description |
|---------|-------------|
| MCP server management | Spawn, monitor, auto-restart stdio MCP servers from a central registry |
| Per-client enhancement | Ollama model routing: Claude Desktop → deepseek-r1, VS Code → qwen2.5-coder, etc. |
| OpenAI-compatible proxy | `/v1/chat/completions` endpoint for desktop apps (Cursor, Raycast, Obsidian) |
| Circuit breakers | 3 failures → OPEN → 30s → HALF_OPEN → recovery; per-server isolation |
| Response caching | SHA256-keyed L1 in-memory LRU cache for enhanced prompts |
| Audit logging | Structured JSON audit trail with security alerts and integrity verification |
| Unified MCP bridge | Single stdio server that aggregates all MCP tools for Claude Desktop |
| HTMX dashboard | Real-time monitoring of server status, cache stats, activity |

## Business Rules

- Enhancement failures are **non-fatal** — the original prompt is always forwarded
- All security-relevant operations produce audit events
- Credentials are stored in macOS Keychain via Python `keyring`, never in plaintext config
- The router is **local-only** (`127.0.0.1`); no public-facing deployment is supported
- API keys for the `/v1/*` proxy use the `sk-prompthub-{client}-*` prefix convention

## Documentation Principle

User-facing documentation (guides, quickstarts, troubleshooting) is written at a **high-school reading level (grade 9–10)**: short sentences, common words, active voice, one action per step, and plain-English analogies for complex concepts. See the `user-manual` agent for the full readability standard.

## Project Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 2 | Complete | Core router, caching, circuit breakers, Ollama enhancement |
| Phase 2.5 | Complete | MCP server management, stdio bridges |
| Phase 3 | Complete | Desktop integration, config generators, documentation pipeline |
| Phase 4 | Complete | HTMX dashboard with real-time monitoring |
| Phase 5 | Complete | OpenAI-compatible API proxy for desktop apps |

## Request Lifecycle

### MCP Proxy (`POST /mcp/{server}/{path}`)
1. Circuit breaker check → reject if OPEN
2. Auto-start server if `auto_start: true` and not running
3. JSON-RPC proxied via stdio bridge to MCP server
4. Success/failure updates circuit breaker state

### OpenAI Proxy (`POST /v1/chat/completions`)
1. Bearer token validation → resolve `client_name`
2. Circuit breaker check (`ollama-proxy`)
3. Enhancement: last user message enhanced via EnhancementService (if `enhance: true`)
4. Forward to Ollama (`localhost:11434/v1/chat/completions`)
5. Stream SSE or return JSON → back to desktop app

### Direct Enhancement (`POST /ollama/enhance`)
1. X-Client-Name header determines Ollama model
2. Cache check (SHA256 of prompt)
3. Ollama request with per-client system prompt
4. Cache result and return
