# Project TODOs

## Now

### Progressive Tool Disclosure (priority: high)

> **Plan:** [`docs/notes/plans/progressive-tool-disclosure.md`](docs/notes/plans/progressive-tool-disclosure.md)
> **Depends on:** Agent-Initiated Server Start.
> **Context:** PromptHub is a router + enhancement middleware rather than a gateway, but lazy-loading tools still reduces tool-context waste. Flagged 2026-05-08 as the next key optimization priority — bridge currently exposes the full tool list from every running server on connect; tier-1/tier-2 disclosure with meta-tool gating cuts initial context by ~80%.

- [ ] Test `notifications/tools/list_changed` in Claude Desktop, Cherry Studio, and VS Code; clients that fail remain on `disclosure: full`.
- [ ] Phase 1: Add `discover_tools` and `load_server_tools` to `mcps/prompthub-bridge.js`, building on `start_server` and `list_available_servers`; add `TOOL_DISCLOSURE` and `TIER1_SERVERS` env vars.
- [ ] Phase 2: Add `tool_profile` to `enhancement-rules.json`, expose `GET /clients/{name}/tool-profile`, and show disclosure mode per client in the dashboard.
- [ ] Phase 3 (optional): Use tool registry `serve_count` to auto-promote frequently used servers to tier 1.

### OpenAI-Compatible Proxy

- [ ] **Cherry Studio auth via PromptHub router stopped working** — was working previously, now Cherry Studio fails to authenticate against `/v1/`. Suspected cause: a proxy setting in Cherry Studio got flipped (it has both direct-LLM and proxy-via-PromptHub modes; the LevelDB-backed config may have reverted). First debug step: capture a request from Cherry Studio with verbose HTTP logging and compare against the `Authorization: Bearer sk-prompthub-cherry-studio-001` shape that should reach `app/router/openai_compat/auth.py`. Verify the api-keys.json entry for cherry-studio is still intact and `enhance: false` (it shouldn't need to be flipped).
- [ ] Support `response_format` passthrough; add `response_format` to `ChatCompletionRequest`, preserve and forward it in `app/router/openai_compat/router.py`, extend `LLMClient.chat_completion()` in `app/router/enhancement/llm_client.py` to accept passthrough options, add tests for `json_object` and `json_schema`, and document backend compatibility and fallback behavior.
- [ ] Audit dropped OpenAI-compatible fields; review whether `frequency_penalty`, `presence_penalty`, `user`, and Responses API structured-output fields should also pass through consistently.

### Review MCPs folder and README

- [ ] Add [algonius-browser](https://github.com/algonius/algonius-browser) server as a lightweight CDP bridge to replace `@browsermcp/mcp` (`stdio`, `auto_start=true`).
- [ ] Uninstall `@browsermcp/mcp` and remove it from `mcp-servers.json` and bridge configs.
- [ ] Set the default auto-start servers to: `memory`, `context7`, `sequential-thinking`, `desktop-commander`, `perplexity-comet`, `algonius-browser`.

## Next

### Bridge-wide `X-Client-ID` consistency

> **Memory:** [`reference_audit_context_headers.md`](~/.claude/projects/-Users-visualval--local-share-prompthub/memory/reference_audit_context_headers.md)
> **Context:** PR #23 caught the `X-Client-Name` (enhancement) vs `X-Client-ID` (audit-context) header drift via smoke test. Only `searchMemoryViaRouter` in `mcps/prompthub-bridge.js` currently sends both. Other bridge endpoints (`fetchRunningServers`, `callPromptHub`, `listAvailableServers`, `startServerViaRouter`) send only `X-Client-Name`. Not currently broken — those endpoints don't filter by audit-context client_id. Becomes a silent-failure trap the moment any future endpoint does.

- [ ] Add `X-Client-ID: CLIENT_NAME` to every `fetch()` call in `mcps/prompthub-bridge.js` (alongside the existing `X-Client-Name`). One-line change per call site, ~5 sites total.
- [ ] Optional: extract a `routerHeaders()` helper so future bridge endpoints can't forget either header.

### Client llm.txt knowledge files

- [ ] Add `<client>-llm.txt` knowledge files for active clients: Claude, Codex, LM Studio, Perplexity Desktop, and VS Code; base each on official docs and client-specific quirks.

### Revise Project README

- [ ] Update `README.md` to reflect the current architecture, active clients, and primary documentation entry points; remove the project status table if it cannot be kept current.

## Later

### Feature: Dashboard Chat Sidecar (`feature/open-webui-chat`)

> **Branch:** `feature/open-webui-chat` (preserved on origin; vision-stage exploration, not active development).
> **Vision:** Add a chat UI sidecar to the dashboard for generating, exploring, and fixing client config files. Could extend to enhancement-rule editing — a wizard component that guides users toward config that matches their workflow rather than blank-page editing of `mcp.json` / `enhancement-rules.json`. Pairs naturally with the existing dashboard observability surface: see what a client is doing, then chat-edit its config in the same view.

### Feature: PromptHub RAG Improvements (`feature/prompthub-rag-improvements`)

> **Branch:** `feature/prompthub-rag-improvements` (local-only; vision-stage exploration).
> **Vision:** Promising direction — needs more learning to fully leverage. Aligns well with integrations like Obsidian (vault as knowledge base) and Raycast (quick recall). Likely composes with the FTS5 memory_search work (PR #23) — RAG could ride on top of the same SQLite/FTS5 foundation, with embedding-based retrieval as the next layer once lexical search is well-understood.

### Refactor and standardize `scripts/` folder

- [ ] Audit `scripts/` for dead, redundant, or misplaced scripts.
- [ ] Reorganize `scripts/` into shallow, component-based groups.
- [ ] Define and apply naming conventions such as `*-install.sh`, `*-diagnose.sh`, and `*-restart.sh`.
- [ ] Update `scripts/README.md` to reflect the final structure, intended usage, and glossary-aligned terminology.

## Deferred Refactors

- [ ] Enhancement service exception handlers — `service.py` `enhance()` has near-identical handlers around lines ~552–559 with different log levels; consider consolidating after unskipping integration tests in `test_enhancement_and_caching.py`.
- [ ] Lifespan function length — `main.py` `lifespan()` is ~97 lines initializing 10 services; split into focused init helpers such as `_init_audit()`, `_init_storage()`, `_init_servers()`, and `_init_enhancement()` after adding startup integration tests.
- [ ] `manage-keys.py` as a `[project.scripts]` entry point — nice-to-have polish. Rename `app/scripts/manage-keys.py` → `manage_keys.py` (Python module names can't contain hyphens), add `[project.scripts] manage-keys = "scripts.manage_keys:main"` to `app/pyproject.toml`, and `pip install -e .` to register a `manage-keys` binary in the venv. Replaces today's shell function `prompthub-keys()` with a proper venv-installed CLI. Worth it once more management CLIs (rotate-tokens, audit-export, etc.) join under `app/router/cli/` or `app/scripts/`.

## Done (2026-05-07)

- [x] ~~Add `start_server` meta-tool to the bridge~~ — Implemented as `prompthub_start_server` in PR #20. Calls `POST /servers/{name}/start`, polls `/servers` until `running` (15 s timeout), refreshes cached server list, and sends `notifications/tools/list_changed` so MCP clients re-fetch tools.
- [x] ~~Add `list_available_servers` meta-tool~~ — Implemented as `prompthub_list_available_servers` in PR #20. Calls `GET /servers` and returns the full payload (running, stopped, failed).
- [x] ~~Add CHANGELOG entry for PR #15~~ — Backfilled in PR #20 under `Unreleased > Added` (`llm_api_key` keyring fallback, `LM_API_TOKEN` env alias).
- [x] ~~Add CHANGELOG entry for PR #16~~ — Backfilled in PR #20 under `Unreleased > Fixed` (Ruff debt cleared, lint CI strictened).
- [x] ~~Add CHANGELOG entry for MCP + qwen-code cleanup~~ — Backfilled in PR #20 across `Unreleased > Added/Changed/Fixed` (PR #18: `applescript-mcp` + `homebrew` added, direct sidecars stripped, `setup.sh`/README aligned, `mcpServers` separated from settings).
- [x] ~~Add CHANGELOG entry for Keychain naming refactor~~ — Backfilled in PR #20 under `Unreleased > Changed` (PR #18: unified `prompthub:<key>/$USER` convention; `manage-keys.py` moved to `app/scripts/`; `manage-keys.py list --all`).

## Done (2026-04-20)

- [x] ~~Glossary Alignment verification pass~~ — Swept `docs/` for stale runtime/model tokens (`Ollama`, `gemma3`, `llama3.2`, `qwen2.5-coder`, `qwen3:14b`); verified glossary terms (`router`, `bridge`, `proxy`, `enhancement`, `privacy level`, `circuit breaker`) are used consistently; findings captured in `docs/notes/research/eval-docs-alignment-audit-2026-04-09.md`. Also reverted 6 over-broad `Ollama` → `LLM` substitutions where `Ollama` was a product name or temporal qualifier (`Ollama-era`).

## Done (2026-04-05)

- [x] ~~Rewrite `mcps/README.md`~~ — Rewritten with accurate 10-server roster, bridge documentation, and keyring patterns. PR #9.
- [x] ~~Tool name prefix~~ — Added `TOOL_PREFIX_ALIASES` to the bridge with built-in `perplexity-comet -> perplexity` alias. PR #10.
- [x] ~~Evaluate `@perplexity-ai/mcp-server`~~ — Parked: uninstalled, evaluation note at `docs/notes/research/eval-perplexity-ai-mcp.md`. PR #9.
- [x] ~~Remove `@brave/brave-search-mcp-server`~~ — Uninstalled. PR #9.
- [x] ~~Remove obsidian-wrapper scripts~~ — Deleted, superseded by keyring env blocks in `mcp-servers.json`. PR #9.
- [x] ~~Add mcp-obsidian as on-demand server~~ — Registered with `auto_start: false`, direct binary + keyring env. PR #9.
- [x] ~~Rewrite `docs/architecture/README.md`~~ — Replaced the stale Ollama-era architecture overview with a glossary-aligned reference centered on the current router/bridge/proxy split, LM Studio runtime, current model roles, and current API surfaces.
- [x] ~~Review dashboard plan docs in `docs/notes/plans/`~~ — Moved the two dashboard idea docs from `docs/notes/dashboard/` into `docs/notes/plans/` and updated them to current LM Studio terminology, model names, and MCP server counts.
- [x] ~~AGENTS.md merged and backup deleted~~ — Merged doc queue, steering docs, commit hygiene, escalation rules from backup; fixed stale client list and removed dead `.firecrawl/` reference.
- [x] ~~llm.txt consolidated~~ — Deleted stale `docs/python-prompthub-guide.txt`; rewrote root `llm.txt` as a passive project snapshot for Perplexity/Desktop Commander.
- [x] ~~LLM.txt router injection evaluated~~ — Sketch moved to `docs/notes/research/`; decision: don’t implement.
- [x] ~~DeepSeek use-case evaluated~~ — Guide moved to `docs/notes/research/deepseek-setup-guide.md`; decision: keep as opt-in Cherry Studio model, don’t wire into pipelines.
- [x] ~~Triage uncommitted files~~ — 175 files committed in PR #4.
- [x] ~~Hygiene audit~~ — Fixed `enabledMcpjsonServers`, purged 31 stale permissions, removed dead CLI refs.
- [x] ~~Model ID migration~~ — LM Studio IDs updated everywhere; DeepSeek card created; Qwen3 embedding archived.
- [x] ~~Client integration tests~~ — Deleted `test_client_integrations.py` and `test_cli.py`; 314 tests passing.
