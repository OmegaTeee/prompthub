# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and semantic versioning.

## [Unreleased]

### Added
- **Cloud enhancement fallback (Path D)**: When Ollama is unavailable, clients with `free_ok` or `any` privacy level fall back to OpenRouter free-tier models (e.g., `deepseek/deepseek-r1-0528:free`). `local_only` clients never leave localhost. Separate circuit breaker for OpenRouter (2 failures/60s).
- **Privacy boundary system (Path C)**: `PrivacyLevel` enum (`local_only`, `free_ok`, `any`) on per-client enhancement rules. `X-Privacy-Level` header can downgrade (more restrictive) but never upgrade. Perplexity and Raycast set to `free_ok`; all others default to `local_only`.
- **Persistent write-through cache (Path B)**: L1 in-memory + L2 SQLite hybrid cache. L2 survives restarts, L1 warmup on startup. Controlled via `CACHE_PERSISTENT=true` setting.
- **Client config .example files (Path A)**: `claude-desktop-config.json.example`, `vscode-settings.json.example`, `raycast-mcp-servers.json.example` for integration test contracts
- `app/tests/test_cloud_fallback.py` — 28 tests for cloud fallback flow, privacy gating, model mapping
- `app/tests/test_privacy_level.py` — 20 tests for privacy enum, downgrade-only semantics, config loading
- `app/tests/test_persistent_cache.py` — 24 tests for write-through cache, L2 persistence, warmup
- `extra_headers` field on `OpenAICompatConfig` — makes `OllamaOpenAIClient` reusable for any OpenAI-compatible provider
- `provider` field on `EnhancementResult` — tracks `"ollama"` or `"openrouter"` for observability
- Cloud model mapping from `cloud-models.json` (`local_models` → free-tier cloud equivalents)
- 5 new settings: `OPENROUTER_ENABLED`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_TIMEOUT`, `OPENROUTER_DEFAULT_MODEL`
- `app/tests/test_mcp_gateway.py` — 8 unit tests for dynamic client factory and gateway construction
- Gateway module docstring documenting the Streamable HTTP request path and dynamic factory pattern

### Changed
- Enhancement service `enhance()` now attempts cloud fallback on all Ollama error paths
- `/ollama/enhance` response includes `privacy_level` and `provider` fields
- `build_mcp_gateway()` now accepts `(supervisor, registry)` — mounts proxies for ALL configured servers, not just connected ones
- Architecture README: corrected `StdioBridge`/`ProcessManager` references to `FastMCPBridge`/`Supervisor`
- Modules README: updated dependency graph, integration test example, and error handling to reflect post-migration server module
- ADR-004: updated `Supervisor` constructor example (no longer takes `ProcessManager`)
- CLAUDE.md: corrected `routing/` module description (empty — routing is in `servers/`)
- Annotated historical audit/feature docs (`ASYNC-AUDIT.md`, `AUDIT-CODE-REVIEW.md`, `SECURITY-FIXES.md`, `KEYRING-INTEGRATION-COMPLETE.md`) with archival notes for removed `process.py`/`bridge.py` references
- Test suite: 153 → 225 passed (12 skipped)

### Fixed
- **MCP gateway stale client references**: Rewrote `mcp_gateway.py` to use dynamic `FastMCPProxy(client_factory=...)` instead of `FastMCP.as_proxy(bridge.client)` — servers now survive restarts and late starts without gateway rebuild
- **Bridge.js tool name truncation**: Fixed `split('_', 2)` dropping tool name segments (e.g., `create_directory` → `create`); now uses `indexOf`/`substring` to split on first underscore only
- **Gateway topology rebuild**: Added `_rebuild_gateway()` in `main.py` for `install_server` and `remove_server` endpoints — gateway re-mounts after topology changes

### Documentation TODO
- [ ] **CLAUDE.md**: Add `X-Privacy-Level` header, `provider` response field, `OPENROUTER_*` env vars
- [ ] **ADR-007**: Cloud fallback decision — why OpenRouter free-tier, why not Together/Groq/direct DeepSeek API
- [ ] **Privacy & cloud fallback guide** (`app/docs/features/`): Privacy levels, per-client assignment, downgrade-only headers, cloud fallback flow, model mapping
- [ ] **`.env.example`**: Add `OPENROUTER_ENABLED`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_TIMEOUT`, `OPENROUTER_DEFAULT_MODEL`
- [ ] **Obsidian vault** (`~/Vault/PromptHub/`): User guide for getting OpenRouter API key and enabling cloud fallback
- [ ] **`app/docs/modules/`**: Update enhancement module docs with privacy boundary and cloud client

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
