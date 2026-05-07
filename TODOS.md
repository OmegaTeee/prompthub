# Project TODOs

## Now

### Backfill CHANGELOG entries

> **Context:** Two recent merges shipped without CHANGELOG entries when the doc queue was skipped during a rapid PR cycle (2026-04-29 session). Both are user-visible enough to warrant a one-line note in `Unreleased`.

- [ ] Add CHANGELOG entry for PR #15 (`fix(settings): resolve llm_api_key from LM_API_TOKEN env or Keychain`): note the new env alias `LM_API_TOKEN` and Keychain fallback for `llm_api_key` (account `lm_api_token` under service `prompthub`); mirrors the existing `openrouter_api_key` resolution chain at [`app/router/config/settings.py`](app/router/config/settings.py).
- [ ] Add CHANGELOG entry for PR #16 (`chore(router): clear Ruff debt and align lint CI`): note the 10 `router/` Ruff errors fixed (E402/F841/F541/I001), the strictening of `ci.yml`'s Lint job (dropped `continue-on-error: true`), removal of duplicate Ruff/mypy sub-steps from `tests.yml`, and deletion of the `claude-code-review` auto-runner workflow.
- [ ] Add CHANGELOG entry for MCP + qwen-code cleanup (2026-05-07 session): `applescript-mcp` (`@peakmojo/applescript-mcp`) and `homebrew` (`brew mcp-server`) added to `app/configs/mcp-servers.json` with `auto_start: false`; direct sidecar entries (`applescript-mcp-server`, `fetch`, `homebrew`, `applescript_mcp`) stripped from `qwen-code`, `claude`, and `vscode` client configs; `qwen-code/setup.sh` filename references fixed (`settings.direct-lmstudio.json` → `settings.direct.json`, `settings.prompthub-router.json` → `settings.router.json`); `qwen-code/README.md` Files list refreshed; `mcpServers` blocks stripped from `settings.direct.json` and `settings.router.json` (now sourced solely from `mcp.json`, matching Qwen Code's preferred separation); literal LM Studio token in `settings.router.json` replaced with `${LM_API_TOKEN}` env var reference; obsolete `QWEN.txt`, `.qwen/`, and `clients/qwen-code/add-mcps.sh` removed.
- [ ] Add CHANGELOG entry for Keychain naming refactor (2026-05-07 session): unified PromptHub credential storage on `service=prompthub:<key>, account=$USER` (was `service=prompthub, account=<key>`); 12 entries migrated; `KeyringManager`, `Settings._get_from_keyring`, and `manage-keys.py` updated to construct service names from a `prompthub:` prefix; `mcp-servers.json` `{source: "keyring"}` entries dropped the now-redundant `service` field; `manage-keys.py list --all` added (shows configured + orphaned + legacy entries); shell helper `keychain_secret()` in `~/.shell_common.sh` extended to a 3-level fallback chain (`prompthub:<key>/$USER` → `prompthub/<key>` → `<KEY-UPPERCASE>/$USER`); shell call sites switched to snake_case keys (`HUGGINGFACE_API_KEY` → `hf_api_key`, `GITHUB_PAT` → `github_token`, etc.); 8 legacy duplicates deleted (greptile, hf, lm_api_token, lmstudio, obsidian×2, openrouter, perplexity from `svce='prompthub'`); 5 redundant new-convention orphans deleted (`lmstudio_api_key`, `cherryin_api_key`, `cherryin_system_access_token`, `github_api_key`, `github_token`); cherryin and github values now sourced solely from the older `svce='prompthub', account=<key>` form via the helper's middle fallback; `manage-keys.py` and its README moved from `scripts/security/` to `app/scripts/` (canonical invocation `python scripts/manage-keys.py` from `app/` with venv active); empty `scripts/security/` removed; drive-by typo `ZED_OPEN_AI_COMPATIBLE_EDIT_PERDICTION_API_KEY` → `..._PREDICTION_...`. Tests `test_settings_keyring.py` (5) + `test_keyring_integration.py` (3) pass.

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
- [ ] `manage-keys.py` as a `[project.scripts]` entry point — nice-to-have polish. Rename `app/scripts/manage-keys.py` → `manage_keys.py` (Python module names can't contain hyphens), add `[project.scripts] manage-keys = "scripts.manage_keys:main"` to `app/pyproject.toml`, and `pip install -e .` to register a `manage-keys` binary in the venv. Replaces today's shell function `prompthub-keys()` with a proper venv-installed CLI. Worth it once more management CLIs (rotate-tokens, audit-export, etc.) join under `app/router/cli/` or `app/scripts/`.

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
