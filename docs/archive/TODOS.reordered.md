# Project TODOs (reordered draft)

> FLAGGED: This file was detected by the rewrite verification pass to contain
> historical model tokens (e.g., `gemma3`, `llama3.2`, `qwen2.5-coder`,
> `qwen3:14b`). These are preserved for context and migration history. See
> `docs/architecture/ADR-008-task-specific-models.md` for the canonical current
> model assignments before performing automated replacements.

Current mapping (editor quick-reference): enhancement →
`qwen3-4b-instruct-2507`; orchestrator (thinking) → `qwen3-4b-thinking-2507`.
When updating historical model mentions in prose, prefer annotating them with
parenthetical mappings (e.g., "llama3.2 (now qwen3-4b-instruct-2507) (now qwen3-4b-instruct-2507)") to
preserve auditability.

## Now

### Agent-Initiated Server Start (priority: high)

> **Context:** On-demand servers (`obsidian`, `chrome-devtools-mcp`, `browsermcp`) don't expose tools until started. Agents currently can't see or start them. This is a prerequisite for effective use of on-demand servers and directly supports Progressive Tool Disclosure Phase 1.

- [ ] Add `start_server` meta-tool to the bridge; call `POST /servers/{name}/start`, wait for the server to register, then refresh the bridge tool list.
- [ ] Add `list_available_servers` meta-tool; call `GET /servers` and return all configured servers, including running, stopped, and failed.

### Progressive Tool Disclosure

> **Plan:** [`docs/notes/plans/progressive-tool-disclosure.md`](docs/notes/plans/progressive-tool-disclosure.md)
> **Depends on:** Agent-Initiated Server Start.
> **Context:** PromptHub is a router + enhancement middleware rather than a gateway, but lazy-loading tools still reduces tool-context waste.

- [ ] Test `notifications/tools/list_changed` in Claude Desktop, Cherry Studio, and VS Code; clients that fail remain on `disclosure: full`.
- [ ] Phase 1: Add `discover_tools` and `load_server_tools` to `mcps/prompthub-bridge.js`, building on `start_server` and `list_available_servers`; add `TOOL_DISCLOSURE` and `TIER1_SERVERS` env vars.
- [ ] Phase 2: Add `tool_profile` to `enhancement-rules.json`, expose `GET /clients/{name}/tool-profile`, and show disclosure mode per client in the dashboard.
- [ ] Phase 3 (optional): Use tool registry `serve_count` to auto-promote frequently used servers to tier 1.

### OpenAI-Compatible Proxy

- [ ] Support `response_format` passthrough; add `response_format` to `ChatCompletionRequest`, preserve and forward it in `app/router/openai_compat/router.py`, extend `LLMClient.chat_completion()` in `app/router/enhancement/llm_client.py` to accept passthrough options, add tests for `json_object` and `json_schema`, and document backend compatibility and fallback behavior.
- [ ] Audit dropped OpenAI-compatible fields; review whether `frequency_penalty`, `presence_penalty`, `user`, and Responses API structured-output fields should also pass through consistently.

### Review MCPs folder and README

- [ ] Add [algonius-browser](https://github.com/algonius/algonius-browser) server as a lightweight CDP bridge to replace `@browsermcp/mcp` (`stdio`, `auto_start=true`).
- [ ] Uninstall `@browsermcp/mcp` and remove it from `mcp-servers.json` and bridge configs.
- [ ] Set the default auto-start servers to: `memory`, `context7`, `sequential-thinking`, `desktop-commander`, `perplexity-comet`, `algonius-browser`.

## Next

### Client llm.txt knowledge files

- [ ] Add `<client>-llm.txt` knowledge files for active clients: Claude, Codex, LM Studio, Perplexity Desktop, and VS Code; base each on official docs and client-specific quirks.

### Glossary Alignment — verification pass

> **Glossary:** [`docs/glossary.md`](docs/glossary.md)
> **Context:** Heavy-lift rewrites are done; this is the cleanup pass to confirm stale runtime/model terms are gone.

- [ ] Grep the full `docs/` tree for `LLM`, `gemma3`, `llama3.2`, `qwen2.5-coder`, `qwen3:14b`, and `llm` (case-insensitive); verify glossary terms like `router`, `bridge`, `proxy`, `enhancement`, `privacy level`, and `circuit breaker` are used consistently; capture findings in one short verification note.

### Revise Project README

- [ ] Update `README.md` to reflect the current architecture, active clients, and primary documentation entry points; remove the project status table if it cannot be kept current.

## Later

### Refactor and standardize `scripts/` folder

- [ ] Audit `scripts/` for dead, redundant, or misplaced scripts.
- [ ] Reorganize `scripts/` into shallow, component-based groups.
- [ ] Define and apply naming conventions such as `*-install.sh`, `*-diagnose.sh`, and `*-restart.sh`.
- [ ] Update `scripts/README.md` to reflect the final structure, intended usage, and glossary-aligned terminology.

## Deferred Refactors

- [ ] Enhancement service exception handlers — `service.py` `enhance()` has near-identical handlers around lines ~552–559 with different log levels; consider consolidating after unskipping integration tests in `test_enhancement_and_caching.py`.
- [ ] Lifespan function length — `main.py` `lifespan()` is ~97 lines initializing 10 services; split into focused init helpers such as `_init_audit()`, `_init_storage()`, `_init_servers()`, and `_init_enhancement()` after adding startup integration tests.

## Done (2026-04-05)

- [x] ~~Rewrite `mcps/README.md`~~ — Rewritten with accurate 10-server roster, bridge documentation, and keyring patterns. PR #9.
- [x] ~~Tool name prefix~~ — Added `TOOL_PREFIX_ALIASES` to the bridge with built-in `perplexity-comet -> perplexity` alias. PR #10.
- [x] ~~Evaluate `@perplexity-ai/mcp-server`~~ — Parked: uninstalled, evaluation note at `docs/notes/research/eval-perplexity-ai-mcp.md`. PR #9.
- [x] ~~Remove `@brave/brave-search-mcp-server`~~ — Uninstalled. PR #9.
- [x] ~~Remove obsidian-wrapper scripts~~ — Deleted, superseded by keyring env blocks in `mcp-servers.json`. PR #9.
- [x] ~~Add mcp-obsidian as on-demand server~~ — Registered with `auto_start: false`, direct binary + keyring env. PR #9.
- [x] ~~Rewrite `docs/architecture/README.md`~~ — Replaced the stale LLM-era architecture overview with a glossary-aligned reference centered on the current router/bridge/proxy split, LM Studio runtime, current model roles, and current API surfaces.
- [x] ~~Review dashboard plan docs in `docs/notes/plans/`~~ — Moved the two dashboard idea docs from `docs/notes/dashboard/` into `docs/notes/plans/` and updated them to current LM Studio terminology, model names, and MCP server counts.
- [x] ~~AGENTS.md merged and backup deleted~~ — Merged doc queue, steering docs, commit hygiene, escalation rules from backup; fixed stale client list and removed dead `.firecrawl/` reference.
- [x] ~~llm.txt consolidated~~ — Deleted stale `docs/python-prompthub-guide.txt`; rewrote root `llm.txt` as a passive project snapshot for Perplexity/Desktop Commander.
- [x] ~~LLM.txt router injection evaluated~~ — Sketch moved to `docs/notes/research/`; decision: don’t implement.
- [x] ~~DeepSeek use-case evaluated~~ — Guide moved to `docs/notes/research/deepseek-setup-guide.md`; decision: keep as opt-in Cherry Studio model, don’t wire into pipelines.
- [x] ~~Triage uncommitted files~~ — 175 files committed in PR #4.
- [x] ~~Hygiene audit~~ — Fixed `enabledMcpjsonServers`, purged 31 stale permissions, removed dead CLI refs.
- [x] ~~Model ID migration~~ — LM Studio IDs updated everywhere; DeepSeek card created; Qwen3 embedding archived.
- [x] ~~Client integration tests~~ — Deleted `test_client_integrations.py` and `test_cli.py`; 314 tests passing.
