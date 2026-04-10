# Project TODOs

## Client llm.txt knowledge files
- [ ] **Find getting-started guides for active clients** — Each client directory should have a `<name>-llm.txt` knowledge file covering config format, MCP transport, and quirks. Three placeholders already have them (cherry-studio, zed, jetbrains). Active clients still need them: Claude, Codex, LM Studio, Perplexity Desktop, VS Code. Source official docs or getting-started guides for each.

## Review MCPs folder and README
- [x] ~~**Rewrite `mcps/README.md`**~~ — Rewritten with accurate 10-server roster, bridge documentation, and keyring patterns. PR #9.
- [x] ~~**Tool name prefix**~~ — Added TOOL_PREFIX_ALIASES to bridge with built-in `perplexity-comet → perplexity` alias. PR #10.
- [x] ~~**Evaluate @perplexity-ai/mcp-server**~~ — Parked: uninstalled, evaluation note at `docs/notes/research/eval-perplexity-ai-mcp.md`. PR #9.
- [x] ~~**Remove @brave/brave-search-mcp-server**~~ — Uninstalled. PR #9.
- [x] ~~**Remove obsidian-wrapper scripts**~~ — Deleted, superseded by keyring env blocks in `mcp-servers.json`. PR #9.
- [x] ~~**Add mcp-obsidian as on-demand server**~~ — Registered with `auto_start: false`, direct binary + keyring env. PR #9.

## Agent-Initiated Server Start (priority: high)

> **Context:** On-demand servers (`obsidian`, `chrome-devtools-mcp`, `browsermcp`) don't expose tools until started. Agents currently can't see or start them. This is a prerequisite for effective use of on-demand servers and directly supports Progressive Tool Disclosure Phase 1.

- [ ] **Add `start_server` meta-tool to the bridge** — A bridge-level tool that calls `POST /servers/{name}/start` on the router, waits for the server to register, then refreshes the bridge's tool list. Agents can then call on-demand server tools in the same session. No `list_changed` notification needed — the bridge controls its own tool list.
- [ ] **Add `list_available_servers` meta-tool** — Returns all servers from `mcp-servers.json` (running + stopped + failed) so agents can see what's available to start. Lightweight: just calls `GET /servers` and formats the response.

## Progressive Tool Disclosure

> **Plan:** [`docs/notes/plans/progressive-tool-disclosure.md`](docs/notes/plans/progressive-tool-disclosure.md)
> **Context:** Compared with [MCPGateway](https://github.com/abdullah1854/MCpGateway) — PromptHub is a router + enhancement middleware (not a gateway), but MCPGateway's lazy-loading idea directly reduces tool context waste.
> **Depends on:** Agent-Initiated Server Start (above) — the `start_server` and `list_available_servers` meta-tools are the foundation for `discover_tools` and `load_server_tools`.

### Insights driving this work

- **MCP protocol constraint:** `tools/list` must return full schemas for every callable tool. Hidden tools can't be called. The `notifications/tools/list_changed` notification is how the bridge dynamically expands the visible tool set mid-session — but only if the client honors it.
- **Per-client tool profiles are natural:** PromptHub already customizes *what the LLM says* per client (enhancement rules). Progressive disclosure extends this to *what tools the LLM sees* per client. Same pattern, different axis.
- **Token math:** ~25 KB post-minification (~7K tokens) for all tools today. Progressive mode with 3 tier-1 servers drops to ~6 KB (~1.7K tokens). The `discover_tools` catalog adds ~2 KB only when called.

### Tasks

- [ ] **Prerequisite: test `list_changed` notification** — Verify Claude Desktop, Cherry Studio, and VS Code re-fetch `tools/list` when the bridge sends `notifications/tools/list_changed`. Clients that don't → stay on `disclosure: full`. This is a 5-minute manual test before writing any code.
- [ ] **Phase 1: meta-tools in the bridge** — Add `discover_tools` and `load_server_tools` to `mcps/prompthub-bridge.js`. Build on `start_server` and `list_available_servers` from the section above. Add `TOOL_DISCLOSURE` env var (`full` | `progressive`) and `TIER1_SERVERS` env var. No router changes needed.
- [ ] **Phase 2: per-client profiles via router** — Add `tool_profile` field to `enhancement-rules.json`. New endpoint `GET /clients/{name}/tool-profile`. Bridge fetches profile at startup. Dashboard shows disclosure mode per client.
- [ ] **Phase 3 (optional): data-driven tier-1** — Use tool registry `serve_count` to auto-promote frequently used servers to tier 1. Nightly job or dashboard button.

## Glossary Alignment — Heavy-Lift Docs Review

> **Glossary:** [`docs/glossary.md`](docs/glossary.md)
> **Context:** Quick fixes applied to ADRs, modules, API, steering, and root docs on 2026-04-05. Two documents need full rewrites (not quick find-replace) because the stale content is deeply embedded in diagrams, flow charts, and benchmarks.

- [x] ~~**Rewrite `docs/architecture/README.md`**~~ — Replaced the stale Ollama-era architecture overview with a glossary-aligned reference centered on the current router/bridge/proxy split, LM Studio runtime, current model roles, and current API surfaces.
- [x] ~~**Review dashboard plan docs in `docs/notes/plans/`**~~ — Moved the two dashboard idea docs from `docs/notes/dashboard/` into `docs/notes/plans/` and updated them to current LM Studio terminology, model names, and MCP server counts.
- [ ] **Post-rewrite verification pass** — After the heavy-lift rewrites above, grep the full `docs/` tree for remaining `Ollama`, `gemma3`, `llama3.2`, `qwen2.5-coder`, `qwen3:14b`, and `ollama` (case-insensitive) to confirm no stale terms remain. Verify all glossary terms (`router`, `bridge`, `proxy`, `enhancement`, `privacy level`, `circuit breaker`) are used consistently.

## Deferred Refactors

- [ ] **Enhancement service exception handlers** — `service.py` `enhance()` has near-identical handlers at lines ~552-559 with different log levels (`warning`/`error`/`exception`). Consider consolidating if log-level distinction proves unnecessary. Unskip integration tests first (`test_enhancement_and_caching.py`).
- [ ] **Lifespan function length** — `main.py` `lifespan()` is ~97 lines (L128→L225) initializing 10 services. Break into focused init helpers (`_init_audit()`, `_init_storage()`, `_init_servers()`, `_init_enhancement()`). Requires adding startup integration tests first to catch initialization order regressions.

## Done (2026-04-05)

- [x] ~~**AGENTS.md merged and backup deleted**~~ — Merged doc queue, steering docs, commit hygiene, escalation rules from backup. Fixed stale client list, removed dead `.firecrawl/` reference.
- [x] ~~**llm.txt consolidated**~~ — Deleted stale `docs/python-prompthub-guide.txt`. Rewrote root `llm.txt` as passive project snapshot for Perplexity/Desktop Commander.
- [x] ~~**LLM.txt router injection evaluated**~~ — Sketch moved to `docs/notes/research/`. Decision: don't implement. Bridge clients have CLAUDE.md; 4B model doesn't benefit.
- [x] ~~**DeepSeek use-case evaluated**~~ — Guide moved to `docs/notes/research/deepseek-setup-guide.md`. Decision: keep as opt-in Cherry Studio model, don't wire into pipelines. Model card created.
- [x] ~~**Triage uncommitted files**~~ — 175 files committed in PR #4. Client folders, CLI deletion, model IDs.
- [x] ~~**Hygiene audit**~~ — Fixed `enabledMcpjsonServers`, purged 31 stale permissions, removed dead CLI refs.
- [x] ~~**Model ID migration**~~ — LM Studio IDs updated everywhere. DeepSeek card created. Qwen3 embedding archived.
- [x] ~~**Client integration tests**~~ — Deleted `test_client_integrations.py` and `test_cli.py`. 314 tests passing.
