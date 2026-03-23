# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and semantic versioning.

## [Unreleased]

### Added
- **`clients/` directory**: Separated client application settings (VS Code, Codex, OpenClaw, Copilot OAI extension, Open WebUI MCPO example) from MCP bridge configs. `mcps/configs/` now holds only MCP bridge configs; `clients/` holds editor prefs, agent configs, and integration examples.
- **`docs/notes/` convention**: Established naming convention (`llm-`, `plan-`, `idea-`, `eval-` prefixes), YAML frontmatter with status lifecycle (`draft` → `review` → `final`), and README. Renamed misnamed `llm-gemma3:4b.md` → `llm-qwen3-14b-model-card.md`, `prompthub-rag-improvement-plan.md` → `plan-rag-improvement.md`.
- **Model cards** for all 5 Ollama models: `qwen3:14b` (orchestrator + OpenClaw), `gemma3:4b` (default enhancement), `gemma3:27b` (Claude Desktop enhancement), `qwen3-coder:30b` (Claude Code enhancement), `bge-m3` (embeddings). Each card documents Ollama manifest, capabilities, parameters, PromptHub roles, and recommendations.
- **LLM stack inventory** (`docs/notes/llm-stack.md`): Rewritten with actual Ollama state, three-layer pipeline docs (orchestrator → enhancement → proxy), per-client enhancement table from `enhancement-rules.json`, OpenClaw experimentation log, model-client pairing guide.
- **OpenClaw client**: API key `sk-prompthub-openclaw-001`, bridge config with `SERVERS` filter (duckduckgo, sequential-thinking, desktop-commander, browsermcp, context7). Configured with `qwen3:14b` as primary model after testing showed `qwen3:8b` and `glm-4.7-flash` inadequate for tool calling.
- **Chrome DevTools MCP server**: Added `chrome-devtools-mcp@latest` to MCP server roster. Connects to a running browser via CDP (`--browserUrl http://127.0.0.1:9222`) for debugging, profiling, performance analysis, network inspection, and browser automation. Set to `auto_start: false` (requires browser with remote debugging enabled). Google telemetry disabled via `--usageStatistics false`.
- **BrowserMCP server**: Added `@browsermcp/mcp` to MCP server roster. Drives existing Chrome tabs via extension WebSocket bridge — supports navigation, clicking, typing, screenshots, and accessibility snapshots. Set to `auto_start: false` (requires Chrome extension connection).
- **Open WebUI integration**: First-class PromptHub client connecting via HTTP (`/v1/` proxy + `/mcp-direct/mcp` Streamable HTTP). API key `sk-prompthub-openwebui-001` with enhancement disabled for lower latency. CLI support (`generate`, `install`, `validate`, `list`), `GET /configs/open-webui` endpoint, dashboard panel with connection status (15s HTMX polling), launch scripts (`start.sh`, `stop.sh`), and macOS LaunchAgent plist. 13 new tests (8 unit, 5 integration).
- **GATEWAY_SERVERS filter**: New `GATEWAY_SERVERS` env var (comma-separated) limits which MCP servers the Streamable HTTP gateway (`/mcp-direct/mcp`) exposes. Empty = all servers. Useful for reducing tool count when connecting smaller models (e.g., gemma3:4b) via Open WebUI. Applied in `build_mcp_gateway()` and respected on gateway rebuild.
- **MCP wrapper scripts** (`mcps/scripts/`): Secure shell wrappers for Obsidian MCP servers using macOS Keychain for API key retrieval. Includes `obsidian-mcp-tools.sh`, `obsidian-rest.sh`, `obsidian.sh`, and a README documenting the wrapper pattern, security benefits of `exec`, and template for new wrappers.
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
- **Scripts promoted to project root**: Moved `app/scripts/` → `scripts/` to sit alongside `docs/` for easier access. Moved `prompthub-start.zsh` and `prompthub-kill.zsh` from workspace root into `scripts/`. Deleted duplicate `open-webui-start.sh` and `open-webui-stop.sh` from root. Updated all references in CLAUDE.md, QUICKSTART.md, README.md, mcps/README.md, Open WebUI guide, LaunchAgent plist, and internal `sys.path`/`dirname` resolution in scripts.
- **LaunchAgent plists fixed**: Router plist symlink was backwards (repo pointed at `~/Library/LaunchAgents/`); reversed so repo is source of truth. Fixed OpenWebUI plist: expanded `~` to absolute paths (launchd doesn't expand tilde), added `WorkingDirectory`, and installed symlink to `~/Library/LaunchAgents/`. Both plists now use the repo copy as the canonical source.
- **Log consolidation**: All runtime logs now write to `logs/` in the project directory. Open WebUI logs moved from `~/.prompthub/open-webui.log` and `~/.prompthub/open-webui-launchd.log` to `logs/openwebui.log` (start script) and `logs/openwebui-stdout.log`/`logs/openwebui-stderr.log` (LaunchAgent). Router logs were already at `logs/router-stdout.log`/`logs/router-stderr.log`.
- **Docs migration to project root**: Moved `app/docs/` → `docs/` so documentation sits above both `app/` and `mcps/`, matching the actual system boundary. Updated all cross-references in CLAUDE.md, AGENTS.md, README.md, QUICKSTART.md, CHANGELOG.md, steering docs, and copilot-instructions.md. Removed `guides` symlink (no longer needed — `docs/guides/` is directly accessible).
- **MCP transport adapters doc**: Renamed `fastmcp-bridge.md` → `mcp-transport-adapters.md` and restructured into three clear sections: (1) Stdio Bridge, (2) Streamable HTTP Gateway, (3) Internal FastMCPBridge — with shared infrastructure (proxy route, cache-through, circuit breaker) in a common section.
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
- **Memory MCP client hardcoded port**: `MemoryMCPClient` was initialized with `base_url="http://localhost:9090"` instead of deriving host/port from `Settings`. Running the router on a non-default port (e.g., `PORT=8080`) caused Memory MCP sync to silently fail. Now derives the URL from `settings.host`/`settings.port` with `0.0.0.0` → `127.0.0.1` translation for loopback connectivity.
- **Script audit fixes**: Fixed broken `sys.path` in `test_security_alerts.py` and `test_keyring_integration.py` (pointed at `manual-tests/` instead of `app/`), stale `"obsidian"` server name → `"obsidian-mcp-tools"` in keyring test, and `((PASS++))` arithmetic crash under `set -e` in `validate-mcp-servers.sh`. Removed redundant `dev/run-tests.sh` (superseded by `test.sh`).
- **Open WebUI port configuration**: Dashboard panel (`_get_open_webui_info()`) now reads port from `~/.prompthub/open-webui.json` instead of hardcoding 3000, so the HTMX widget correctly detects Open WebUI on non-default ports
- **Open WebUI start script port precedence**: Fixed variable ordering in `start.sh` so the JSON config port is consulted before the hardcoded default (`env var > config file > 3000`)
- **Project path references**: Updated `~/.local/share/prompthub` → `~/prompthub` across 4 user guides, `validate-mcp-servers.sh`, and root start script (`$HOME/PromptHub` → `$HOME/prompthub`)
- **QUICKSTART.md script references**: Corrected `start-prompthub.zsh`/`kill-prompthub.zsh` to match actual filenames `prompthub-start.zsh`/`prompthub-kill.zsh`; fixed missing `~/` prefix in api-keys.json path
- **Ollama setting defaults**: Changed `ollama_host` from `host.docker.internal` (Docker) to `localhost` (local macOS), `ollama_model` from `llama3.2:3b` (not installed) to `gemma3:4b`, and `ollama_timeout` from 30s to 120s to match `.env` and documentation
- **Configs README phantom file**: Removed 4 references to nonexistent `mcp-servers-keyring.json`; replaced credentials section with actual inline keyring pattern used in `mcp-servers.json`
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
- [x] **`docs/modules/`**: Update modules README with `routes/` package, enhancement privacy/cloud info
- [x] **`structure.md`**: Update steering doc with `routes/` package and updated line counts
- [ ] **Privacy & cloud fallback guide** (`docs/features/`): Privacy levels, per-client assignment, downgrade-only headers, cloud fallback flow, model mapping
- [ ] **Obsidian vault** (`~/Vault/PromptHub/`): User guide for getting OpenRouter API key and enabling cloud fallback

---

## [0.1.4] - 2026-02-14

### Added
- Steering documents for AI agents (`.claude/steering/product.md`, `tech.md`, `structure.md`)
- Complete OpenAPI 3.0 spec coverage (43 endpoints, including `/v1/*` proxy)
- Module coverage analysis (`docs/modules/COVERAGE-ANALYSIS.md`)

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
- Stale MCP paths updated from `~/.local/share/mcps/` to `~/prompthub/mcps/`

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
