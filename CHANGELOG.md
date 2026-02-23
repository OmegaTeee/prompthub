# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and semantic versioning.

## [Unreleased]

### Fixed
- **MCP gateway stale client references**: Rewrote `mcp_gateway.py` to use dynamic `FastMCPProxy(client_factory=...)` instead of `FastMCP.as_proxy(bridge.client)` — servers now survive restarts and late starts without gateway rebuild
- **Bridge.js tool name truncation**: Fixed `split('_', 2)` dropping tool name segments (e.g., `create_directory` → `create`); now uses `indexOf`/`substring` to split on first underscore only
- **Gateway topology rebuild**: Added `_rebuild_gateway()` in `main.py` for `install_server` and `remove_server` endpoints — gateway re-mounts after topology changes

### Added
- `app/tests/test_mcp_gateway.py` — 8 unit tests for dynamic client factory and gateway construction
- Gateway module docstring documenting the Streamable HTTP request path and dynamic factory pattern

### Changed
- `build_mcp_gateway()` now accepts `(supervisor, registry)` — mounts proxies for ALL configured servers, not just connected ones
- Architecture README: corrected `StdioBridge`/`ProcessManager` references to `FastMCPBridge`/`Supervisor`
- Modules README: updated dependency graph, integration test example, and error handling to reflect post-migration server module
- ADR-004: updated `Supervisor` constructor example (no longer takes `ProcessManager`)
- CLAUDE.md: corrected `routing/` module description (empty — routing is in `servers/`)
- Annotated historical audit/feature docs (`ASYNC-AUDIT.md`, `AUDIT-CODE-REVIEW.md`, `SECURITY-FIXES.md`, `KEYRING-INTEGRATION-COMPLETE.md`) with archival notes for removed `process.py`/`bridge.py` references

---

## [0.1.4] - 2026-02-14

### Added
- Steering documents for AI agents (`.claude/steering/product.md`, `tech.md`, `structure.md`)
- Complete OpenAPI 3.0 spec coverage (43 endpoints, including `/v1/*` proxy)
- Module coverage analysis (`app/docs/modules/COVERAGE-ANALYSIS.md`)

### Changed
- Documentation restructuring: fixed broken links, promoted completed features, archived stale docs
- Established documentation lifecycle pattern (reviews → features → archive)

### Fixed
- Stale `guides/` references across ~15 files updated to point to Obsidian vault

### Removed
- `PROJECT.md` (content incorporated into `.claude/steering/product.md`)

## [0.1.3] - 2026-02-13

### Changed
- Migrated user guides from `guides/` to Obsidian vault (`~/Vault/PromptHub/`)
- 28 user guide files created across 7 sections (Getting Started, Core Setup, Integrations, Workflows, Testing, Migration, Reference)
- New Cursor IDE integration guide added to Obsidian vault

### Removed
- `guides/` directory (50 files, 22,489 lines)

## [0.1.2] - 2026-02-12

### Added
- **Cursor IDE integration**: global `~/.cursor/mcp.json` with unified bridge
- **Obsidian MCP server**: configured with REST API plugin, SSL certificates
- **Greptile MCP server**: keyring-based API key authentication

### Fixed
- OLLAMA_HOST normalization in settings (handles `http://localhost:11434` from env)
- Plaintext secrets removed from `.mcp.json`, stored in macOS Keychain
- Stale MCP paths updated from `~/.local/share/mcps/` to `~/.local/share/prompthub/mcps/`

### Security
- GitHub token and API keys moved to keyring, removed from config files

## [0.1.1] - 2026-02-12

### Changed
- Renamed project from `agenthub` to `prompthub` across 169 files
- Standardized credential management on Python `keyring` (macOS Keychain)

## [0.1.0] - 2026-02-12

### Added
- **Core router**: FastAPI application at `localhost:9090`
- **MCP server management**: spawn, monitor, auto-restart stdio MCP servers
- **Prompt enhancement**: per-client Ollama model routing (deepseek-r1, qwen2.5-coder)
- **OpenAI-compatible proxy**: `/v1/chat/completions` for desktop apps (Cursor, Raycast, Obsidian)
- **Circuit breakers**: per-server resilience (CLOSED → OPEN → HALF_OPEN)
- **Response caching**: SHA256-keyed L1 in-memory LRU cache
- **HTMX dashboard**: real-time monitoring UI
- **Audit system**: structured JSON logging, security alerts, integrity verification (score 9.0/10)
- **Unified MCP bridge**: single stdio server aggregating all MCP tools
- **Client configurations**: Claude Desktop, VS Code, Raycast setup scripts
- **Documentation pipeline**: multi-step Ollama → Sequential Thinking → Obsidian workflow
- **7 MCP servers**: context7, desktop-commander, sequential-thinking, memory, deepseek-reasoner, obsidian, duckduckgo
- **30 API endpoints** + 10 dashboard endpoints + 3 OpenAI proxy endpoints
- **14 test files**: unit + integration tests (100% pass rate)
- **5 Architecture Decision Records** (ADRs)
- **OpenAPI 3.0 specification**

---

<!-- Release entries will be prepended here by scripts/release.sh -->
