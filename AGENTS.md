# AGENTS.md

Shared contract for every AI coding agent in this repo (Claude Code, Codex, OpenCode, Copilot).
`CLAUDE.md` imports this file and adds Claude Code–specific setup. Terms follow [docs/glossary.md](docs/glossary.md).

## What PromptHub is

A local MCP router for macOS. One FastAPI service on `localhost:9090` that:

- runs and proxies a fleet of stdio MCP servers behind one endpoint (plus a Node stdio bridge, `mcps/prompthub-bridge.js`, that aggregates them for clients);
- enhances prompts per client through a local LLM server (LM Studio by default, any OpenAI-compatible backend works);
- exposes an OpenAI-compatible `/v1/` proxy with bearer auth;
- wraps everything in circuit breakers, an L1/L2 cache, audit logging, and an HTMX dashboard.

Per-client behaviour (model, tool disclosure, privacy level) is resolved **server-side** from `app/configs/enhancement-rules.json`. Clients only need a near-identical bridge entry with their `CLIENT_NAME`. Prefer improving shared server-side logic over client-specific hacks.

## Checkouts: dev vs. running daemon

| Path | Role |
| --- | --- |
| `~/workspaces/prompthub` | Development checkout (this repo). Edit and test here. |
| `~/.local/share/prompthub` (symlinked as `~/prompthub`) | Deployed checkout. The LaunchAgent `com.prompthub.router` and client bridge configs run from here. |

Changes reach the daemon only after they are merged to `main` and deployed with `app/scripts/prompthub-update.zsh`. Never edit the deployed checkout from a dev task unless asked.

## Layout

```
app/                    Python project (run all Python commands from here)
├── router/             FastAPI package (modular monolith, see below)
├── tests/              pytest: unit/ + integration/
├── configs/            mcp-servers.json, enhancement-rules.json, api-keys.json, cloud-models.json
├── templates/          Jinja2 + HTMX dashboard
├── scripts/            prompthub-update.zsh, diagnose.sh, manage-keys.py, prompthub-start/kill.zsh, test.sh
└── pyproject.toml      pytest/ruff/mypy config; deps in requirements.txt
mcps/                   Node stdio bridge (prompthub-bridge.js) + npm-installed MCP servers
docs/                   glossary, architecture/ (ADRs), api/ (openapi.yaml), modules/, features/,
                        guides/ (3 user references), agent-guides/, wiki/, notes/
```

Client MCP config files are no longer kept in this repo; the config pattern is documented in [docs/guides/getting-started.md](docs/guides/getting-started.md).

## Commands

```bash
cd app && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cd mcps && npm install                                 # MCP server packages

cd app && uvicorn router.main:app --reload --port 9090 # run (dev)
cd app && pytest tests/ -v                             # test
cd app && ruff check router/ && ruff format router/    # lint/format
cd app && mypy router/                                 # types
node --check mcps/prompthub-bridge.js                  # bridge syntax
curl http://localhost:9090/health                      # verify
./app/scripts/diagnose.sh                              # full-stack diagnostics

./app/scripts/prompthub-update.zsh --dry-run           # plan a deploy to ~/.local/share/prompthub
./app/scripts/prompthub-update.zsh                     # deploy: ff-pull, deps, restart, health check
launchctl kickstart -k gui/$(id -u)/com.prompthub.router   # restart deployed daemon only
```

CI (`.github/workflows/ci.yml`) runs ruff and pytest on Python 3.11 and 3.12.

## Architecture (`app/router/`)

| Module | Purpose |
| --- | --- |
| `main.py` | App factory: lifespan init, middleware, router wiring |
| `routes/` | health, servers, mcp_proxy, enhancement, audit, pipelines, clients (tool/model profiles) |
| `config/` | Pydantic `Settings` (`.env`), JSON config loading |
| `servers/` | MCP server lifecycle via FastMCP + StdioTransport (spawn, monitor, restart) |
| `resilience/` | Circuit breaker (3 failures → OPEN, 30s → HALF_OPEN, success → CLOSED) |
| `cache/` | L1 in-memory LRU + L2 SQLite write-through |
| `enhancement/` | OpenAI-compatible LLM client, per-client rules, OpenRouter cloud fallback, token budget |
| `orchestrator/` | Pre-enhancement intent classifier (thinking model) |
| `openai_compat/` | `/v1/` proxy (chat completions, responses, models) |
| `memory/` | Session memory (SQLite facts, memory blocks, MCP sync) |
| `tool_registry/` | SQLite cache of `tools/list` snapshots with archival |
| `dashboard/` | HTMX observability UI |
| `pipelines/` | Documentation generation workflow |
| `middleware/` | Audit context, activity log, request timeouts |
| `audit.py`, `audit_integrity.py`, `security_alerts.py` | Structured audit log, SHA256 tamper checks, anomaly alerts |
| `keyring_manager.py` | macOS Keychain credentials |

**Request flow** for `POST /mcp/{server}/{path}`: circuit breaker check → `tools/list` served from tool registry if cached → auto-start server if configured → JSON-RPC via FastMCP bridge → cache `tools/list` result → update breaker.

**Key patterns**

- Async everywhere (`httpx`, `asyncio`); never `requests`.
- Route modules use factory-with-getter-callables: `create_X_router(get_service=lambda: service)`, so globals resolve after lifespan init.
- Tiered timeouts: httpx client 120s → middleware 60s (180s for slow paths) → LLM keep-alive 5 min.
- Privacy boundary: `PrivacyLevel` (`local_only`, `free_ok`, `any`). `local_only` never leaves localhost; the others may fall back to OpenRouter free tier (ADR-007).
- Model profiles: `model_profiles` in `enhancement-rules.json` (`daemon`, `coder`, `instruct`) mapped per client via `model_profile`. `Settings.llm_model` is the code-level fallback (ADR-008).
- Tool disclosure: per-client `tool_profile` (`full` or `progressive` + `tier1_servers`), served at `GET /clients/{name}/tool-profile`. Bridge env vars (`TOOL_DISCLOSURE`, `TIER1_SERVERS`) override it, so leave them unset unless pinning on purpose.
- Bridge minifies tool `inputSchema` (drops description/title/examples/default) before returning to clients.
- Enhancement input capped at 4,096 tokens (`TokenBudget`).

Full endpoint list: [docs/api/openapi.yaml](docs/api/openapi.yaml). ADRs: [docs/architecture/](docs/architecture/).

## Configuration

| File | Holds |
| --- | --- |
| `app/.env` (from `.env.example`) | `HOST`, `PORT`, `LLM_HOST`/`LLM_PORT`/`LLM_MODEL`/`LLM_ORCHESTRATOR_MODEL`/`LLM_TIMEOUT`, `DATA_DIR`, cache and breaker tuning, config paths, `OPENROUTER_*`, `LOG_LEVEL` |
| `app/configs/mcp-servers.json` | MCP server registry (command, args, env, `auto_start`, `restart_on_failure`) |
| `app/configs/enhancement-rules.json` | Per-client prompts, privacy level, `model_profile`, `tool_profile`; top-level `model_profiles` |
| `app/configs/api-keys.json` | Bearer tokens for `/v1/` (client name, enhance flag) |
| `app/configs/cloud-models.json` | Local → free-tier cloud model mapping |

Persistent state lives under `~/.prompthub/` (`DATA_DIR`): `cache.db`, `activity.db`, `memory.db`, `tool_registry.db`, `audit.log`, `audit_checksums.json`. Storage classes take `db_path: Path | None = None` and resolve `get_settings()` lazily so tests can pass `tmp_path`.

## Code style

- Python 3.11+, type hints required, 88-char lines (ruff format).
- `logging`, never `print()`.
- No new global state; inject dependencies. Never hardcode config; add it to `Settings`.
- Don't invent new config shapes when an existing pattern fits.

## Working rules

- Smallest effective validation first; don't claim success without running the command or inspecting the artifact.
- Routing/transport changes: test the happy path and at least one failure/fallback path.
- One logical change per commit. Changelog entries go under `## [Unreleased]` in `CHANGELOG.md` (Added / Changed / Fixed / Removed), one sentence each.
- If code and docs disagree, trust the code and fix the doc.

**Stop and ask the user** before: changing auth, credentials, or audit behaviour; removing or renaming a public endpoint; touching more than ~20 files in one change.

## Documentation

| Location | Purpose |
| --- | --- |
| `docs/guides/` | Exactly three user references: `getting-started.md`, `features.md`, `operations.md`. Update in place; don't add files. |
| `docs/architecture/` | ADRs and design docs |
| `docs/api/` | OpenAPI spec, integration examples |
| `docs/agent-guides/` | Short agent-facing references (project map, build/test/verify, config locations, MCP routing) |
| `docs/wiki/` | LLM-maintained knowledge wiki (`/wiki-*` commands) |
| `docs/notes/` | Working notes, research, plans; not authoritative |

### Post-implementation doc queue

After a feature, fix, or structural change, run the applicable steps (independent, can run in parallel):

| Change type | 1. `CHANGELOG.md` | 2. Code docs (`code-docs` agent) | 3. User guide (`user-manual` agent) |
| --- | --- | --- | --- |
| New feature | Yes | Yes | Yes |
| Bug fix | Yes | If code changed | If user-facing |
| Refactor | If notable | Yes | No |
| Config change | Yes | No | If user-facing |
| Test-only | No | No | No |

Step 2 touches only new/modified code (docstrings, type hints, comments on non-obvious logic). Step 3 updates the relevant file in `docs/guides/`.

### Pruning policy

When asked to simplify or clean up docs, delete rather than annotate. Git history is the archive (`git log --follow -p -- <path>`).

- Cut stale prose, dead links, and redirect chains. Active docs describe the current state only.
- No `FLAGGED:` / `HISTORICAL:` / `DEPRECATED:` annotations and no "(formerly X)" asides.
- Exception: keep historical names in **config and code** where real environments still use them (env-var aliases such as `AliasChoices("LLM_API_KEY", "LM_API_TOKEN")`, keyring keys, deprecated endpoints). Pure-legacy aliases nobody uses can go.
