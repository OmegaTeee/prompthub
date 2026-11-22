# Operations

Troubleshooting, local model guidance, advanced configuration, and diagnostics. Setup is in [getting-started.md](getting-started.md); feature behavior is in [features.md](features.md).

- [Diagnostics](#diagnostics)
- [Troubleshooting](#troubleshooting)
- [Local LLM and model recommendations](#local-llm-and-model-recommendations)
- [Advanced configuration](#advanced-configuration)

## Diagnostics

Work through these in order; most problems show up in the first two.

```bash
curl -s http://localhost:9090/health          # router, llm, cache, servers
app/scripts/diagnose.sh                       # node, bridge, router, servers, client configs (PASS/FAIL lines)
tail -f <log-dir>/router-stderr.log           # log dir is whatever your LaunchAgent / start script uses
open http://localhost:9090/dashboard          # servers, cache, circuit breakers, LLM, memory, tool registry
```

Useful endpoints:

| Endpoint | Shows |
| --- | --- |
| `GET /health` | `status`, `services.router`, `services.llm` (`up`/`down`), cache hit rate, per-server summary |
| `GET /servers` | MCP servers and state |
| `GET /circuit-breakers`, `POST /circuit-breakers/{name}/reset` | Breaker state and manual reset |
| `GET /llm/stats` | Enhancement cache and LLM health |
| `GET /tools/stats` | Tool registry (cached servers, total tools) |
| `GET /audit/activity?client_id=<name>&limit=50` | Persistent HTTP activity log |
| `GET /audit/integrity/verify` | Audit log checksum verification |
| `GET /security/alerts` | Recent security alerts |
| `GET /clients/{name}/tool-profile`, `/model-profile` | Resolved per-client profiles |

Repo scripts (all in `app/scripts/`): `diagnose.sh`, `manage-keys.py` (Keychain credentials), `prompthub-start.zsh`, `prompthub-kill.zsh`, `lms-start.sh` (loads the router's model; run at login by `com.prompthub.lms.plist`), `test.sh`, `router/validate-mcp-servers.sh`, `router/restart_mcp_servers.py`, `system/launchctl-env-audit.sh`, `system/audit-maintenance.sh`. See `app/scripts/README.md`.

To collect a report for an issue:

```bash
{ app/scripts/diagnose.sh; curl -s http://localhost:9090/health; tail -n 100 <log-dir>/router-stderr.log; } > diagnostics.txt 2>&1
```

Remove secrets before sharing it.

## Troubleshooting

### Router not reachable on localhost:9090

```bash
lsof -i :9090                                   # who owns the port
app/scripts/prompthub-kill.zsh                  # stop uvicorn and bridge
cd app && source .venv/bin/activate && uvicorn router.main:app --host 127.0.0.1 --port 9090 --reload
```

- Port in use by a stale process: kill it, or change `PORT` in `app/.env` and update `PROMPTHUB_URL` in client configs.
- `HOST=0.0.0.0` is a bind address, not a target. Connect to `localhost` or `127.0.0.1`.
- Daemon: `launchctl kickstart -k gui/$(id -u)/com.prompthub.router`, then read the stderr log for the startup error.
- Syntax or import errors after an update: `cd app && python -m py_compile router/main.py && pip install -r requirements.txt`.

### `"llm": "down"` or LLM connection failed

```bash
curl http://localhost:1234/v1/models            # use LLM_HOST / LLM_PORT from app/.env
lms ps                                          # models loaded in LM Studio
```

Start LM Studio and enable the server (Developer tab). Confirm `LLM_HOST` and `LLM_PORT` match. The check is the OpenAI-style `/v1/models` path, which Ollama also serves (default port 11434). The router keeps working without the LLM; enhancement falls back per [privacy level](features.md#privacy-levels-and-cloud-fallback).

### 401 Unauthorized on `/v1/`

The bearer token is missing, malformed, or not in `app/configs/api-keys.json`. After editing the file run `curl -X POST http://localhost:9090/v1/api-keys/reload`. See [API tokens](getting-started.md#api-tokens).

### 404 or model not found

The requested `model` is not loaded or downloaded. List what the server has with `curl http://localhost:9090/v1/models`, fetch with `lms get <model>`, and check the model name in `app/configs/enhancement-rules.json` (or run `curl http://localhost:9090/clients/<name>/model-profile`).

### Enhancement not happening

1. The client rule has `"enabled": true` (all ship disabled).
2. The entry point is opted in: `enhance: true` on the API key, `X-Enhance: true`, or `AUTO_ENHANCE_MCP=true`.
3. `/health` shows `llm: up`.
4. Call `POST /llm/enhance` directly and read the `error` field.

### Requests time out or are slow

- Disable enhancement for latency-sensitive keys (`"enhance": false` in `api-keys.json`, then reload).
- Raise `LLM_TIMEOUT` (default 120) in `app/.env`; cloud fallback has `OPENROUTER_TIMEOUT`. The middleware has its own request timeout (60s default, 180s for slow paths).
- Check the model is fully loaded (`lms ps`) and the machine is not CPU or memory bound (`top -o %CPU`).
- Use a smaller model or a lighter [model profile](features.md#model-profiles).

### Tools missing in the client

- Fully restart the client; MCP clients cache tool lists.
- `curl http://localhost:9090/servers` shows whether the server is running. `chrome-devtools-mcp` is not auto-started: `curl -X POST http://localhost:9090/servers/chrome-devtools-mcp/start`.
- Progressive mode hides most tools by design; see [Progressive tool disclosure](features.md#progressive-tool-disclosure). Check `curl http://localhost:9090/clients/<name>/tool-profile`.
- A stale list: `curl -X POST http://localhost:9090/tools/<server>/refresh`.
- A server crashing on start: run its command from `app/configs/mcp-servers.json` by hand to see the error. Servers behind an open circuit breaker are rejected; `POST /circuit-breakers/<name>/reset` after fixing the cause.
- `SERVERS` / `EXCLUDE_TOOLS` in the bridge env can hide tools unintentionally.

### "Tool has an output schema but did not return structured content"

Seen with `sequential-thinking` through some bridge clients. Update `mcps/prompthub-bridge.js` to the current version (`cd mcps && npm install`), restart the client and run `app/scripts/prompthub-kill.zsh` then `prompthub-start.zsh`.

### Token variable missing in a GUI app

Shell tokens do not reach GUI apps; see [Launchctl token environment](getting-started.md#launchctl-token-environment).

### Database is locked

Two router processes are using `~/.prompthub/memory.db` (or another SQLite file).

```bash
pgrep -fl "uvicorn router.main:app"             # expect one
lsof ~/.prompthub/memory.db
sqlite3 ~/.prompthub/memory.db "PRAGMA integrity_check;"   # expect: ok
```

Kill extra uvicorn processes and restart.

### Session not found

Session IDs are full UUIDs. List with `curl http://localhost:9090/sessions`. If the database is unrecoverable, `rm ~/.prompthub/memory.db` and restart; this deletes all sessions and facts.

### Circuit breaker stays open

Default: 3 failures open it (`CB_FAILURE_THRESHOLD`), 30 seconds to half-open (`CB_RECOVERY_TIMEOUT`), one success closes it. Fix the underlying server or LLM, then reset via `POST /circuit-breakers/<name>/reset`.

## Local LLM and model recommendations

PromptHub talks to any OpenAI-compatible server through `LLM_HOST` and `LLM_PORT`. LM Studio is the default (port 1234); Ollama works by pointing `LLM_PORT` at 11434.

Which model is used where is configured, not hardcoded. Read these instead of this guide when in doubt:

| Role | Where it is set |
| --- | --- |
| Enhancement default (code-level safety net) | `LLM_MODEL` in `app/.env`, default in `app/router/config/settings.py` |
| Named bundles: `daemon`, `coder`, `instruct` | `model_profiles` in `app/configs/enhancement-rules.json` |
| Per-client choice | `model_profile` or `model` on the client's rule |
| Orchestrator | `LLM_ORCHESTRATOR_MODEL` (a thinking model) |

Current profile mapping: `daemon` uses a 4B instruct model, `coder` a 9B coder model (used by `vscode`, `claude-code`, `codex`), `instruct` an 8B instruct model. Rationale: [ADR-008](../architecture/ADR-008-task-specific-models.md).

Guidance for choosing models:

- **Rewriter**: small instruct model (about 4B). Fast, deterministic at low temperature, no reasoning tokens. Models under 1B often echo or truncate input.
- **Orchestrator**: a thinking model of similar size; it classifies, so latency matters more than depth.
- **Coder profile**: use a larger coder model only for clients where rewrite quality on code prompts matters and you have the memory for it.
- **Memory**: on a 16 GB machine keep enhancement and orchestrator models at about 4B and load one at a time; 32 GB or more can hold a 9B coder plus the 4B models.
- Keep one LM Studio server for everything; models load on first request, so the first call after a cold start is slow. Keep models loaded with LM Studio's keep-alive setting (the router assumes about 5 minutes).

LM Studio CLI:

```bash
lms ls                       # downloaded models
lms get <model-identifier>   # download
lms ps                       # loaded models
lms load <model>             # load
lms unload <model>           # free memory
lms server start             # start the API server
```

After changing models, run `curl http://localhost:9090/clients/<name>/model-profile` and one `POST /llm/enhance` request to confirm the resolved model responds.

## Advanced configuration

### Adding or changing MCP servers

Edit `app/configs/mcp-servers.json` (override path with `MCP_SERVERS_CONFIG`). Per server: `command`, `args`, `env`, `auto_start`, `restart_on_failure`. Then restart the router, or manage one server live:

```bash
curl -X POST http://localhost:9090/servers/<name>/start    # also: stop, restart
curl -X DELETE http://localhost:9090/servers/<name>
```

Validate the fleet with `app/scripts/router/validate-mcp-servers.sh` and restart all with `app/scripts/router/restart_mcp_servers.py`.

### Per-client behavior

All in `app/configs/enhancement-rules.json`: `enabled`, `model` / `model_profile`, `system_prompt`, `temperature`, `max_tokens`, `privacy_level`, `tool_profile`. Add a new client by copying the closest existing rule; the bridge's `CLIENT_NAME` must match the key.

### Bridge tuning

Set in the client's MCP `env` block (see [bridge env vars](getting-started.md#the-bridge-entry)): `TOOL_DISCLOSURE`, `TIER1_SERVERS`, `SERVERS`, `EXCLUDE_TOOLS`, `MINIFY_SCHEMAS`, `DESC_MAX_LENGTH`, `TOOL_PREFIX_ALIASES`. Tool names are prefixed by server (`desktop-commander_list_directory`); built-in aliases remove double prefixes such as `perplexity-comet_comet_ask` to `comet_ask`.

### Cache

L1 in-memory LRU (`CACHE_MAX_SIZE`) plus L2 SQLite write-through in `$DATA_DIR/cache.db` (`CACHE_PERSISTENT=false` for L1 only). Clear it from the dashboard or `POST /dashboard/actions/clear-cache`. Tool lists are cached in the tool registry (`$DATA_DIR/tool_registry.db`, 24-hour TTL, expired snapshots archived):

```bash
curl http://localhost:9090/tools/stats
curl -X POST http://localhost:9090/tools/<server>/refresh
curl -X DELETE http://localhost:9090/tools/<server>
curl -X POST http://localhost:9090/tools/archive
curl -X POST "http://localhost:9090/tools/cleanup?retention_days=30"
```

### Data directory

Everything persistent lives under `DATA_DIR` (default `~/.prompthub/`). Each file can be overridden independently:

| File | Setting | Used by |
| --- | --- | --- |
| `cache.db` | `CACHE_DB_PATH` | Persistent cache, enhancement cache |
| `activity.db` | `ACTIVITY_DB_PATH` | HTTP activity log |
| `memory.db` | `MEMORY_DB_PATH` | Session memory |
| `tool_registry.db` | `TOOL_REGISTRY_DB_PATH` | Tool registry |
| `audit.log` | `AUDIT_LOG_PATH` | Structured audit log |
| `audit_checksums.json` | `AUDIT_CHECKSUM_PATH` | Audit tamper detection |

Back up by copying the directory while the router is stopped.

### Credentials

Secrets live in macOS Keychain (service `prompthub:<key>`), not in `.env` or config files:

```bash
python app/scripts/manage-keys.py list          # --all also lists orphaned and legacy entries
```

Known keys: `openrouter_api_key`, `obsidian_api_key`, `obsidian_authentication`, `hf_api_key`, `lm_api_token`. Every access is audit-logged.

### Audit and security

All security-relevant actions (admin actions, credential access, config changes) are written as structured JSON to `audit.log` with `request_id`, `client_id` (from `X-Client-ID`), and `client_ip`. Checksums detect tampering (`GET /audit/integrity/verify`). Real-time alerts fire on 3 or more repeated failures in 5 minutes, 5 or more credential accesses in a minute, credential probing, and config changes (`GET /security/alerts`). Maintenance: `app/scripts/system/audit-maintenance.sh`.

### Development

```bash
cd app && source .venv/bin/activate
pytest tests/ -v          # tests
mypy router/              # types
ruff check router/ && ruff format router/
```

New route modules follow the factory pattern `create_X_router(get_service=lambda: service)` so globals resolve after lifespan startup. Settings go through the `Settings` class, never hardcoded.

### Upgrades

The daemon runs from the deployed checkout (`~/.local/share/prompthub`). Update it with:

```bash
app/scripts/prompthub-update.zsh --dry-run   # show incoming commits and any blockers
app/scripts/prompthub-update.zsh             # fast-forward, reinstall changed deps, restart, health check
app/scripts/prompthub-update.zsh --rollback  # return to the previously deployed commit
```

The script refuses to update when:

- an incoming change touches a file you edited locally in the deployed checkout (back the edit up, or pass `--stash`);
- the update deletes a file that a client config symlinks to, for example VS Code or Codex settings that point into `clients/` (move that config out first, or pass `--ignore-links`).

It reinstalls Python deps only when `app/requirements.txt` changed, and runs `npm ci` only when `mcps/package*.json` changed. Deploys are logged to `~/.prompthub/deploy-history.log`, which `--rollback` reads. Other flags: `--yes` skips the prompt, `--no-restart` leaves the daemon alone. Override the target with `PROMPTHUB_DEPLOY_DIR`.

Fully restart MCP clients afterward so the bridge reloads.
