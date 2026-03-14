# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and semantic versioning.

## [Unreleased]

### Added
- **Open WebUI integration**: First-class PromptHub client connecting via HTTP (`/v1/` proxy + `/mcp-direct/mcp` Streamable HTTP). API key `sk-prompthub-openwebui-001` with enhancement enabled (gemma3:4b, local_only privacy). CLI support (`generate`, `install`, `validate`, `list`), `GET /configs/open-webui` endpoint, dashboard panel with connection status (15s HTMX polling), launch scripts (`start.sh`, `stop.sh`), and macOS LaunchAgent plist. 13 new tests (8 unit, 5 integration).
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
- **main.py split (Path E)**: Reduced main.py from 1,421 → 505 lines by extracting 30+ route handlers into 7 focused modules under `router/routes/` (health, servers, mcp_proxy, enhancement, audit, pipelines, client_configs). Uses existing factory-with-getter-callables DI pattern.
- Enhancement service `enhance()` now attempts cloud fallback on all Ollama error paths
- `/ollama/enhance` response includes `privacy_level` and `provider` fields
- `build_mcp_gateway()` now accepts `(supervisor, registry)` — mounts proxies for ALL configured servers, not just connected ones
- Architecture README: corrected `StdioBridge`/`ProcessManager` references to `FastMCPBridge`/`Supervisor`
- Modules README: updated dependency graph, integration test example, and error handling to reflect post-migration server module
- ADR-004: updated `Supervisor` constructor example (no longer takes `ProcessManager`)
- CLAUDE.md: updated with `routes/` module, privacy boundary, cloud fallback, `X-Privacy-Level` header, `OPENROUTER_*` env vars, `cloud-models.json` config
- Annotated historical audit/feature docs (`ASYNC-AUDIT.md`, `AUDIT-CODE-REVIEW.md`, `SECURITY-FIXES.md`, `KEYRING-INTEGRATION-COMPLETE.md`) with archival notes for removed `process.py`/`bridge.py` references
- Test suite: 153 → 225 passed (12 skipped)

### Fixed
- **MCP gateway stale client references**: Rewrote `mcp_gateway.py` to use dynamic `FastMCPProxy(client_factory=...)` instead of `FastMCP.as_proxy(bridge.client)` — servers now survive restarts and late starts without gateway rebuild
- **Bridge.js tool name truncation**: Fixed `split('_', 2)` dropping tool name segments (e.g., `create_directory` → `create`); now uses `indexOf`/`substring` to split on first underscore only
- **Gateway topology rebuild**: Added `_rebuild_gateway()` in `main.py` for `install_server` and `remove_server` endpoints — gateway re-mounts after topology changes

- **Token budget for enhancement** (`context_window.py`): Caps enhancement input at 4,096 tokens — truncates at word boundaries with notice. Prevents wasting context on prompt rewrites for large inputs. `TokenBudget` class with `fits()`, `truncate()`, `summary()` methods.
- `register_model()` — register model context windows at runtime without editing source
- `app/tests/unit/test_context_window.py` — 20+ tests covering budget formula, truncation, word boundary snapping, registry mutations
- `app/templates/partials/token-budget.html` — Dashboard panel showing per-client token budgets
- `app/scripts/test.sh` — Test runner script (unit/integration/coverage/watch modes)
- Cloud model registry entries for task-specific models: `gemma3:4b`, `gemma3:27b`, `qwen3-coder:30b`, `qwen3:14b` with cloud upgrade/equivalent mappings
- `obsidian-mcp-tools` server entry in `mcp-servers.json` (keyring-sourced API key)
- API keys for `claude-code` and `obsidian` clients
- Project-level agent specs: `code-docs`, `user-manual` (`.claude/agents/`)

### Changed
- **Data directory**: Cache DB moved from `/tmp/prompthub/cache.db` to `~/.prompthub/cache.db` via new `DATA_DIR` setting — persistent storage that survives reboots
- **`.mcp.json` consolidation**: Replaced 5 individual MCP server entries with single `prompthub` bridge — all tools now route through the PromptHub router for circuit breaking, caching, and audit
- **API key naming**: Renamed `*-dev001` keys to `*-001` across configs and docs
- **MCP client configs**: Replaced `claude-desktop-example.json` and `perplexity-mcp.json` with cleaner `claude-desktop.json`, `claude-code.json`, `perplexity.json`
- **LaunchAgent plist**: Changed from inline file to symlink pointing at `~/Library/LaunchAgents/`
- **Workspace**: Replaced `notes` symlink with Obsidian vault as VS Code workspace folder
- Enhancement `cache_db_path` fallback now reads from `settings.cache_db_path` (single source of truth)
- Disabled enhancement on raycast and vscode API keys (was enabled)
- CLAUDE.md: added token budget pattern, enhancement module description, available agents section, table formatting

### Removed
- `mcps/configs/claude-desktop-example.json` (replaced by `claude-desktop.json`)
- `mcps/configs/claude_desktop_config.json` (dangling symlink to Claude's live config)
- `mcps/configs/perplexity-mcp.json` (replaced by `perplexity.json`)
- `notes` symlink (replaced by workspace folder)

### Documentation TODO
- [x] **CLAUDE.md**: Add `X-Privacy-Level` header, `provider` response field, `OPENROUTER_*` env vars, `routes/` module, privacy/cloud patterns
- [x] **ADR-007**: Cloud fallback decision — why OpenRouter free-tier, why not Together/Groq/direct DeepSeek API
- [x] **`.env.example`**: Add `OPENROUTER_ENABLED`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_TIMEOUT`, `OPENROUTER_DEFAULT_MODEL`, `CACHE_PERSISTENT`, `CACHE_DB_PATH`, `DATA_DIR`
- [x] **`app/docs/modules/`**: Update modules README with `routes/` package, enhancement privacy/cloud info
- [x] **`structure.md`**: Update steering doc with `routes/` package and updated line counts
- [ ] **Privacy & cloud fallback guide** (`app/docs/features/`): Privacy levels, per-client assignment, downgrade-only headers, cloud fallback flow, model mapping
- [ ] **Obsidian vault** (`~/Vault/PromptHub/`): User guide for getting OpenRouter API key and enabling cloud fallback

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
