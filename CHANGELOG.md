# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and semantic versioning.

## [Unreleased]

### Security
- **Keyring migration for external API keys** (PR #5): Moved `OPENROUTER_API_KEY`, `OBSIDIAN_API_KEY`, `HF_API_KEY` from plaintext `.env` to macOS Keychain via Python `keyring` (service=`prompthub`). `Settings.model_post_init` now resolves `openrouter_api_key` from keyring when not set in env. Removed `CHERRYIN_API_KEY` (unused).
- **Auto-discovery in `manage-keys.py`**: Replaced hardcoded `KNOWN_KEYS` list with `discover_keys()` that scans `mcp-servers.json` for `{"source": "keyring"}` references plus a `SETTINGS_KEYS` dict for router-level keys. `list` command now shows which server or service consumes each key.

### Fixed
- **Obsidian MCP wrapper Keychain mismatch**: Wrapper scripts in `mcps/obsidian-wrapper/` used `security -a $USER -s "key_name"` but Python `keyring` stores as `security -s "prompthub" -a "key_name"`. These are different Keychain entries — wrappers could never find keys stored via `manage-keys.py`. Fixed all three wrapper scripts to use matching parameters.
- **`KeyringManager.delete_credential` crash on missing keys**: `keyring.delete_password()` throws `PasswordDeleteError` when the key doesn't exist. Now caught separately and returns `True` with `not_found` audit status instead of failing.
- **`localhost` vs `127.0.0.1` bind address**: Changed default `HOST` from `127.0.0.1` to `0.0.0.0` (accepts both IPv4 and IPv6). Added startup warning in `main.py` when `HOST=127.0.0.1` — macOS resolves `localhost` to `::1` (IPv6) which fails against IPv4-only bind.
- **Broken `test_process_env_config` assertions**: Test asserted keys that weren't in the test config. Fixed to match actual test data.

### Added
- **Per-client `setup.sh` scripts**: Each client directory now has a self-contained shell script that creates symlinks (for symlink-safe clients) or prints setup instructions (for GUI/shared-config clients). Scripts are idempotent and self-documenting — header comments declare source, target, and strategy.
- **`scripts/diagnose.sh`**: Pure-shell replacement for `python -m cli diagnose`. Checks node, bridge file, router health, server status, and per-client config symlinks. Auto-discovers clients by scanning `clients/*/setup.sh`.

### Removed
- **Python CLI** (`app/cli/`): Removed all 9 modules (main, models, generator, installer, validator, profiles, diagnostics, __init__, __main__) and `tests/test_cli.py` (91 tests). Replaced by per-client `setup.sh` scripts and `scripts/diagnose.sh`.
- **`/configs/*` API endpoints**: Removed `app/router/routes/client_configs.py` and its 5 HTTP endpoints (`/configs/claude-desktop`, `/configs/vscode`, `/configs/vscode-tasks`, `/configs/raycast`, `/configs/open-webui`). Client configs now live as static files in `clients/`.
- **`typer` dependency**: Removed from `requirements.txt` (was only used by CLI).

### Added (prior)
- **OpenCode client support**: New `ClientType.opencode` with `~/.opencode.json` config path, `type: stdio` extra field, and merge install strategy. OpenCode uses `["KEY=VALUE"]` array format for env vars (unlike the dict format used by all other clients) — handled transparently via new `env_as_array` property on `ClientType` and conversion in `wrap_for_client()`.
- **OpenCode enhancement profile**: Code-focused, Git-aware prompt rewriting (`enhancement-rules.json`). API key `sk-prompthub-opencode-001` with `enhance: true`.
- **OpenCode MCP config**: `clients/opencode/mcp.json` (bridge config with array env) and `clients/opencode/opencode.json` (LM Studio provider template with keyring placeholder).

### Fixed
- **LLM auth dropped by enhancement service**: `EnhancementService.__init__()` reconstructed `LLMConfig` from individual fields but omitted `extra_headers`, silently dropping the `Authorization` header. This caused `LLM: down` health status whenever LM Studio required auth. The OpenAI-compatible proxy and orchestrator were unaffected because they build their own httpx clients directly. Fixed by copying `extra_headers` through the reconstruction.
- **`LLM_HOST=localhost` → `127.0.0.1`**: Prevents IPv6 resolution issues when LM Studio listens on IPv4 only.

### Changed
- **Architecture and active docs refreshed for current terminology**: Rewrote `docs/architecture/README.md` around the current router/bridge/proxy split, moved dashboard refactor notes under `docs/notes/plans/`, cleaned current guides and client READMEs to match the repo-managed setup workflow, and labeled historical ADR/research documents so stale terms no longer read as current guidance.
- **LM Studio planner template**: Rewrote `clients/lm-studio/prompt_templates/planner.txt` to match the lightweight task-template format used by the other LM Studio presets and documented it in the template README.
- **LM Studio chat presets**: Rewrote the task presets in `clients/lm-studio/prompt_templates/` with consistent metadata, higher token budgets, clearer workflow-specific instructions, and an updated README for the on-disk template set.
- **5 new CLI clients**: `lm-studio`, `zed`, `jetbrains`, `codex`, `cherry-studio` added to `ClientType` enum. Each has `config_path()`, `config_key_path`, `install_strategy`, `extra_entry_fields`, and `is_bridge_client` properties. Cherry Studio is an HTTP client (like Open WebUI) connecting via `/v1/responses`. Codex uses TOML — `generate`/`install` raise `NotImplementedError` with a pointer to the manual config file.
- **`repo_dir()` method on `ClientType`**: Returns `clients/<name>/` relative to workspace root, preparing for per-client folder restructuring.
- **`build_cherry_studio_config()`**: Connection settings builder for Cherry Studio (mirrors `build_open_webui_config()`), targeting the `/v1/responses` endpoint.
- **28 new CLI tests** (63 → 91): Properties for all new clients, `wrap_for_client` for Zed/JetBrains, Cherry Studio generation, Codex `NotImplementedError`, generic merge, symlink install, JSONC parsing.

### Changed
- **Data-driven `wrap_for_client`**: Replaced if/elif chain with generic nesting using `client_type.config_key_path` tuple. Handles all formats: `mcpServers` (Claude/Cursor/Raycast/LM Studio), `mcp.servers` (VS Code), `context_servers` (Zed), `servers` (JetBrains). Adding future clients requires zero function changes.
- **Generic `ConfigInstaller._merge_generic()`**: Replaced `_merge_standard()` + `_merge_vscode()` with a single method navigating any key path depth. Supports all current and future config formats.
- **Symlink install strategy**: `ConfigInstaller` auto-detects symlink-safe clients (LM Studio, Cursor, Raycast) via `install_strategy` property. Writes config to `repo_dir()` and creates a symlink at the app's config path, making the repo the source of truth.
- **JSONC support**: `ConfigInstaller._load_jsonc()` and `ConfigValidator._strip_jsonc()` strip `//` comments and trailing commas, enabling merge/validation of Zed's `settings.json`.
- **Multi-format `ConfigValidator`**: `validate_config()` searches all known key paths (`mcpServers`, `mcp.servers`, `context_servers`, `servers`) instead of hardcoding two. `validate_file()` falls back to JSONC stripping on parse failure.
- **Multi-client `Diagnostician`**: `_check_installed_configs()` iterates all bridge clients with existing config files, replacing the single hardcoded Claude Desktop check.
- **CLI `list` command**: Now shows install strategy (`bridge, merge` / `bridge, symlink` / `http, merge`) for each client.

### Added (prior)
- **Local LLM recommendations guide** (`docs/guides/10-local-llm-recommendations.md`): Role-based model selection guide covering 8 use-case roles (Fast Chat, Reasoning, Coding, Assistant, Agent, Inline, Research, Embedding), 7 model families (Qwen3, Llama 4, Gemma 3, Phi-4, Mistral/Devstral, DeepSeek, GPT-OSS), quantization trade-offs with RAM formula, hardware requirement tables for 8/16/32/64 GB tiers, and PromptHub's current setup rationale.
- **New model cards**: `llm-qwen3-4b-2507`, `llm-qwen3-4b-thinking-2507`, `emb-nomic-embed-text-v1.5`, `emb-qwen3-embedding-0.6b` in `docs/notes/models/`. Removed 6 stale cards (gemma3-4b, gemma3-27b, qwen3-14b, qwen3-coder-30b, qwen35-2b, bge-m3).

### Changed
- **Simplified model inventory**: Reduced from 7 models to 4. All clients now use `qwen/qwen3-4b-2507` for enhancement (was per-client: gemma3:4b/gemma3:27b/qwen3-coder:30b). Orchestrator moved from `qwen3-14b-mlx` (14B, 40K ctx) to `qwen/qwen3-4b-thinking-2507` (4B thinking variant, 262K ctx). Total loaded memory: ~5 GB (down from ~13 GB+). No JIT model swapping — both LLMs stay resident.
- **LM Studio docs alignment**: Fixed reasoning field name in `/v1/responses` adapter — LM Studio v0.3.23+ uses `message.reasoning` (not `reasoning_content`). Now checks both fields for cross-server compatibility.
- **Documentation model audit**: Updated model references across 16+ documentation files (CLAUDE.md, steering/tech.md, ADR-008, 7 user guides, README.md, QUICKSTART.md, OLLAMA-OPENAI-API.md). Replaced all Ollama-style `model:tag` names with LM Studio `publisher/model` format. ADR-008 updated with 2026-03-28 simplification addendum.
- **Enhancement deduplication**: Extracted shared enhancement logic from `/v1/chat/completions` and `/v1/responses` into `_maybe_enhance()` helper — eliminates code duplication and drift risk.
- **Context window registry**: Simplified from 7 model entries to 2 (`qwen/qwen3-4b-2507`, `qwen/qwen3-4b-thinking-2507`), both with 262K context.
- **Cloud model local mappings**: Replaced 8 stale local model entries in `cloud-models.json` with 2 current models and their cloud fallback mappings.
- **LM Studio models inventory**: Updated `docs/notes/models/lm-studio-models.json` to reflect 4-model setup with engine versions (mlx-llm v1.4.0, llama.cpp v2.8.0) and loaded status.
- **.env.example**: Updated default model to `qwen/qwen3-4b-2507`, fixed "Ollama" comment to "LLM server".
- **`LLM_ORCHESTRATOR_MODEL` env var**: Orchestrator model is now configurable via `.env` instead of hardcoded in `agent.py`. Default: `qwen/qwen3-4b-thinking-2507`. Follows the same `Settings` → `Field` → `AliasChoices` pattern as `LLM_MODEL`.
- **Refactored duplicated code** (-87 lines net): Extracted `_handle_llm_error()` shared by `/v1/chat/completions` and `/v1/responses`; consolidated 3 identical `_restart/_start/_stop_server` helpers into parameterized `_server_action()`; extracted `_validated_server_action()` in dashboard router; extracted `_parse_json_response()` from nested orchestrator JSON parsing.
- **31 new unit tests** (125 → 156): `_parse_json_response()` (7 tests), `_handle_llm_error()` (4 tests), `_flatten_content()` (7 tests), `_build_responses_response()` edge cases (6 tests), `_server_action()` + thin wrappers (7 tests).

### Fixed
- **`temperature=0` bug in `/v1/responses`**: `body.temperature or 0.7` treated `0.0` as falsy, silently overriding deterministic output requests. Fixed to explicit `None` check.
- **SSE error JSON escaping**: Streaming error messages used hand-escaped string formatting that broke on newlines and backslashes. Replaced with `json.dumps()`.
- **JSON parse error in LLMClient**: `response.json()` on non-JSON responses (e.g., HTML error pages from misconfigured proxy) raised unhandled `JSONDecodeError`. Now caught and wrapped in `LLMError` with body preview.
- **Empty choices crash in `/v1/responses`**: `_build_responses_response()` accessed `choices[0]` without guard — empty LLM responses caused `IndexError`. Added null-safety with graceful empty response.

---

### Added (prior)
- **`clients/` directory**: Separated client application settings (VS Code, Codex, OpenClaw, Copilot OAI extension, Open WebUI MCPO example) from MCP bridge configs. `mcps/configs/` now holds only MCP bridge configs; `clients/` holds editor prefs, agent configs, and integration examples.
- **`docs/notes/` convention**: Established naming convention (`llm-`, `plan-`, `idea-`, `eval-` prefixes), YAML frontmatter with status lifecycle (`draft` → `review` → `final`), and README. Renamed misnamed `llm-gemma3:4b.md` → `llm-qwen3-14b-model-card.md`, `prompthub-rag-improvement-plan.md` → `plan-rag-improvement.md`.
- **Model cards** for all 5 local models: `qwen3:14b` (orchestrator + OpenClaw), `gemma3:4b` (default enhancement), `gemma3:27b` (Claude Desktop enhancement), `qwen3-coder:30b` (Claude Code enhancement), `bge-m3` (embeddings). Each card documents manifest, capabilities, parameters, PromptHub roles, and recommendations.
- **LLM stack inventory** (`docs/notes/llm-stack.md`): Rewritten with actual LM Studio state, three-layer pipeline docs (orchestrator → enhancement → proxy), per-client enhancement table from `enhancement-rules.json`, OpenClaw experimentation log, model-client pairing guide.
- **OpenClaw client**: API key `sk-prompthub-openclaw-001`, bridge config with `SERVERS` filter (duckduckgo, sequential-thinking, desktop-commander, browsermcp, context7). Configured with `qwen3:14b` as primary model after testing showed `qwen3:8b` and `glm-4.7-flash` inadequate for tool calling.
- **Chrome DevTools MCP server**: Added `chrome-devtools-mcp@latest` to MCP server roster. Connects to a running browser via CDP (`--browserUrl http://127.0.0.1:9222`) for debugging, profiling, performance analysis, network inspection, and browser automation. Set to `auto_start: false` (requires browser with remote debugging enabled). Google telemetry disabled via `--usageStatistics false`.
- **BrowserMCP server**: Added `@browsermcp/mcp` to MCP server roster. Drives existing Chrome tabs via extension WebSocket bridge — supports navigation, clicking, typing, screenshots, and accessibility snapshots. Set to `auto_start: false` (requires Chrome extension connection).
- **Open WebUI integration**: First-class PromptHub client connecting via HTTP (`/v1/` proxy + `/mcp-direct/mcp` Streamable HTTP). API key `sk-prompthub-openwebui-001` with enhancement disabled for lower latency. CLI support (`generate`, `install`, `validate`, `list`), `GET /configs/open-webui` endpoint, dashboard panel with connection status (15s HTMX polling), launch scripts (`start.sh`, `stop.sh`), and macOS LaunchAgent plist. 13 new tests (8 unit, 5 integration).
- **GATEWAY_SERVERS filter**: New `GATEWAY_SERVERS` env var (comma-separated) limits which MCP servers the Streamable HTTP gateway (`/mcp-direct/mcp`) exposes. Empty = all servers. Useful for reducing tool count when connecting smaller models (e.g., gemma3:4b) via Open WebUI. Applied in `build_mcp_gateway()` and respected on gateway rebuild.
- **MCP wrapper scripts** (`mcps/scripts/`): Secure shell wrappers for Obsidian MCP servers using macOS Keychain for API key retrieval. Includes `obsidian-mcp-tools.sh`, `obsidian-rest.sh`, `obsidian.sh`, and a README documenting the wrapper pattern, security benefits of `exec`, and template for new wrappers.
- **Cloud enhancement fallback (Path D)**: When the LLM server is unavailable, clients with `free_ok` or `any` privacy level fall back to OpenRouter free-tier models (e.g., `deepseek/deepseek-r1-0528:free`). `local_only` clients never leave localhost. Separate circuit breaker for OpenRouter (2 failures/60s).
- **Privacy boundary system (Path C)**: `PrivacyLevel` enum (`local_only`, `free_ok`, `any`) on per-client enhancement rules. `X-Privacy-Level` header can downgrade (more restrictive) but never upgrade. Perplexity and Raycast set to `free_ok`; all others default to `local_only`.
- **Persistent write-through cache (Path B)**: L1 in-memory + L2 SQLite hybrid cache. L2 survives restarts, L1 warmup on startup. Controlled via `CACHE_PERSISTENT=true` setting.
- **Client config .example files (Path A)**: `claude-desktop-config.json.example`, `vscode-settings.json.example`, `raycast-mcp-servers.json.example` for integration test contracts
- `app/tests/test_cloud_fallback.py` — 28 tests for cloud fallback flow, privacy gating, model mapping
- `app/tests/test_privacy_level.py` — 20 tests for privacy enum, downgrade-only semantics, config loading
- `app/tests/test_persistent_cache.py` — 24 tests for write-through cache, L2 persistence, warmup
- `extra_headers` field on `OpenAICompatConfig` — makes `LLMClient` reusable for any OpenAI-compatible provider
- `provider` field on `EnhancementResult` — tracks `"llm_server"` or `"openrouter"` for observability
- Cloud model mapping from `cloud-models.json` (`local_models` → free-tier cloud equivalents)
- 5 new settings: `OPENROUTER_ENABLED`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_TIMEOUT`, `OPENROUTER_DEFAULT_MODEL`
- `app/tests/test_mcp_gateway.py` — 8 unit tests for dynamic client factory and gateway construction
- Gateway module docstring documenting the Streamable HTTP request path and dynamic factory pattern

### Changed (prior)
- **LLM backend abstraction**: Renamed all internal "Ollama" references to backend-agnostic "LLM" naming. Deleted native Ollama API client (~230 lines) and thinking-token NDJSON→SSE shim (~140 lines). One OpenAI-compatible code path works with LM Studio, Ollama, or any `/v1/` server. Settings: `LLM_HOST`, `LLM_PORT`, `LLM_MODEL`, `LLM_TIMEOUT` (old `OLLAMA_*` names still work as aliases). Routes: `/ollama/enhance` → `/llm/enhance`, `/ollama/stats` → `/llm/stats`, `/ollama/orchestrate` → `/llm/orchestrate`. Dashboard: "Ollama Models" → "Local Models".
- **Docs: LM Studio migration**: Removed user-facing references to Ollama and updated guides to recommend LM Studio as the local LLM provider (docs/guides, QUICKSTART.md, README.md). Added LM Studio CLI examples (`lms get`, `lms server start`) and switched enhancement examples to `/llm/enhance`.
- **Default enhancement model → qwen3.5:2b**: Replaced `gemma3:4b` with `qwen3.5:2b` (2.3B, Q8_0, 2.7 GB) as the default enhancement model across 6 clients (vscode, raycast, perplexity, cursor, comfyui, open-webui). Better instruction-following for text rewriting at lower resource cost. Fallback chain: `qwen3.5:2b → gemma3:27b → null`. Settings default updated. Cloud model mapping added. Model card created.
- **Raycast AI Chat provider**: Added `qwen3.5:2b` as second model in `clients/raycast-ai-providers.yaml` for fast text rewriting via Raycast prompt commands (Improve Writing, Change Tone, etc.).
- **Symlinks flipped to source-in-project**: All 8 client config symlinks were backwards (project symlinked to client location). Reversed so real files live in `clients/` and `mcps/configs/` (git-tracked), and client apps read through symlinks at their expected paths (e.g., `~/.config/raycast/mcp.json` → `~/prompthub/mcps/configs/raycast-mcp.json`). Exception: `vscode-ide.json` stays as inward symlink since VS Code's `settings.json` is a shared system file. Updated both READMEs with symlink convention docs.
- **Raycast AI provider config**: Added `clients/raycast-ai-providers.yaml` for Raycast Chat custom AI provider pointing to PromptHub's `/v1/` OpenAI-compatible proxy. Fixed 401 auth errors caused by `Bearer ` prefix duplication in the API key value.
- **MCP server cards**: Added 8 server cards in `docs/notes/servers/` documenting all MCP servers — tools, client availability, integration notes, and comparisons (browsermcp vs chrome-devtools-mcp).
- **`docs/notes/` subfolder reorganization**: Split flat `docs/notes/` into `models/`, `servers/`, `research/`, `plans/`, `dashboard/` subdirectories. Updated README with tables indexing all 23 files.
- **Scripts promoted to project root**: Moved `app/scripts/` → `scripts/` to sit alongside `docs/` for easier access. Moved `prompthub-start.zsh` and `prompthub-kill.zsh` from workspace root into `scripts/`. Deleted duplicate `open-webui-start.sh` and `open-webui-stop.sh` from root. Updated all references in CLAUDE.md, QUICKSTART.md, README.md, mcps/README.md, Open WebUI guide, LaunchAgent plist, and internal `sys.path`/`dirname` resolution in scripts.
- **LaunchAgent plists fixed**: Router plist symlink was backwards (repo pointed at `~/Library/LaunchAgents/`); reversed so repo is source of truth. Fixed OpenWebUI plist: expanded `~` to absolute paths (launchd doesn't expand tilde), added `WorkingDirectory`, and installed symlink to `~/Library/LaunchAgents/`. Both plists now use the repo copy as the canonical source.
- **Log consolidation**: All runtime logs now write to `logs/` in the project directory. Open WebUI logs moved from `~/.prompthub/open-webui.log` and `~/.prompthub/open-webui-launchd.log` to `logs/openwebui.log` (start script) and `logs/openwebui-stdout.log`/`logs/openwebui-stderr.log` (LaunchAgent). Router logs were already at `logs/router-stdout.log`/`logs/router-stderr.log`.
- **Docs migration to project root**: Moved `app/docs/` → `docs/` so documentation sits above both `app/` and `mcps/`, matching the actual system boundary. Updated all cross-references in CLAUDE.md, AGENTS.md, README.md, QUICKSTART.md, CHANGELOG.md, steering docs, and copilot-instructions.md. Removed `guides` symlink (no longer needed — `docs/guides/` is directly accessible).
- **MCP transport adapters doc**: Renamed `fastmcp-bridge.md` → `mcp-transport-adapters.md` and restructured into three clear sections: (1) Stdio Bridge, (2) Streamable HTTP Gateway, (3) Internal FastMCPBridge — with shared infrastructure (proxy route, cache-through, circuit breaker) in a common section.
- **main.py split (Path E)**: Reduced main.py from 1,421 → 505 lines by extracting 30+ route handlers into 7 focused modules under `router/routes/` (health, servers, mcp_proxy, enhancement, audit, pipelines, client_configs). Uses existing factory-with-getter-callables DI pattern.
- Enhancement service `enhance()` now attempts cloud fallback on all LLM server error paths
- `/llm/enhance` response includes `privacy_level` and `provider` fields
- `build_mcp_gateway()` now accepts `(supervisor, registry)` — mounts proxies for ALL configured servers, not just connected ones
- Architecture README: corrected `StdioBridge`/`ProcessManager` references to `FastMCPBridge`/`Supervisor`
- Modules README: updated dependency graph, integration test example, and error handling to reflect post-migration server module
- ADR-004: updated `Supervisor` constructor example (no longer takes `ProcessManager`)
- CLAUDE.md: updated with `routes/` module, privacy boundary, cloud fallback, `X-Privacy-Level` header, `OPENROUTER_*` env vars, `cloud-models.json` config
- Annotated historical audit/feature docs (`ASYNC-AUDIT.md`, `AUDIT-CODE-REVIEW.md`, `SECURITY-FIXES.md`, `KEYRING-INTEGRATION-COMPLETE.md`) with archival notes for removed `process.py`/`bridge.py` references
- Test suite: 153 → 225 passed (12 skipped)

### Fixed (prior)
- **Memory MCP client hardcoded port**: `MemoryMCPClient` was initialized with `base_url="http://localhost:9090"` instead of deriving host/port from `Settings`. Running the router on a non-default port (e.g., `PORT=8080`) caused Memory MCP sync to silently fail. Now derives the URL from `settings.host`/`settings.port` with `0.0.0.0` → `127.0.0.1` translation for loopback connectivity.
- **Script audit fixes**: Fixed broken `sys.path` in `test_security_alerts.py` and `test_keyring_integration.py` (pointed at `manual-tests/` instead of `app/`), stale `"obsidian"` server name → `"obsidian-mcp-tools"` in keyring test, and `((PASS++))` arithmetic crash under `set -e` in `validate-mcp-servers.sh`. Removed redundant `dev/run-tests.sh` (superseded by `test.sh`).
- **Open WebUI port configuration**: Dashboard panel (`_get_open_webui_info()`) now reads port from `~/.prompthub/open-webui.json` instead of hardcoding 3000, so the HTMX widget correctly detects Open WebUI on non-default ports
- **Open WebUI start script port precedence**: Fixed variable ordering in `start.sh` so the JSON config port is consulted before the hardcoded default (`env var > config file > 3000`)
- **Project path references**: Updated `~/.local/share/prompthub` → `~/prompthub` across 4 user guides, `validate-mcp-servers.sh`, and root start script (`$HOME/PromptHub` → `$HOME/prompthub`)
- **QUICKSTART.md script references**: Corrected `start-prompthub.zsh`/`kill-prompthub.zsh` to match actual filenames `prompthub-start.zsh`/`prompthub-kill.zsh`; fixed missing `~/` prefix in api-keys.json path
- **LLM setting defaults**: Changed `llm_host` from `host.docker.internal` (Docker) to `localhost` (local macOS), `llm_model` from `llama3.2:3b` (not installed) to `gemma3:4b`, and `llm_timeout` from 30s to 120s to match `.env` and documentation
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
- LLM_HOST normalization in settings (handles `http://localhost:11434` from env; also accepts OLLAMA_HOST for backward compatibility)
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
- **Prompt enhancement**: per-client LLM model routing (deepseek-r1, qwen2.5-coder)
- **OpenAI-compatible proxy**: `/v1/chat/completions` for desktop apps (Cursor, Raycast, Obsidian)
- **Circuit breakers**: per-server resilience (CLOSED → OPEN → HALF_OPEN)
- **Response caching**: SHA256-keyed L1 in-memory LRU cache
- **HTMX dashboard**: real-time monitoring UI
- **Audit system**: structured JSON logging, security alerts, integrity verification (score 9.0/10)
- **Unified MCP bridge**: single stdio server aggregating all MCP tools
- **Client configurations**: Claude Desktop, VS Code, Raycast setup scripts
- **Documentation pipeline**: multi-step LLM enhancement → Sequential Thinking → Obsidian workflow
- **7 MCP servers**: context7, desktop-commander, sequential-thinking, memory, deepseek-reasoner, obsidian, duckduckgo
- **30 API endpoints** + 10 dashboard endpoints + 3 OpenAI proxy endpoints
- **14 test files**: unit + integration tests (100% pass rate)
- **5 Architecture Decision Records** (ADRs)
- **OpenAPI 3.0 specification**

---

<!-- Release entries will be prepended here by scripts/release.sh -->
