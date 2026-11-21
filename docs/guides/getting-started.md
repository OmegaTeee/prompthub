# Getting Started

Install PromptHub, run the router, and connect an MCP client. Terms such as router, bridge, and proxy are defined in the [glossary](../glossary.md).

```text
MCP client --stdio--> prompthub-bridge.js --HTTP--> router (localhost:9090) --stdio--> MCP servers
                                                        |
                                                        +--> local LLM server (LM Studio, port 1234)
```

- [Prerequisites](#prerequisites)
- [Install](#install)
- [Run the router](#run-the-router)
- [Verify](#verify)
- [API tokens](#api-tokens)
- [Connecting clients](#connecting-clients)
- [Launchctl token environment](#launchctl-token-environment)

## Prerequisites

| Requirement | Install |
| --- | --- |
| macOS | |
| Python 3.11+ | `brew install python` |
| Node.js | `brew install node` |
| Local LLM server (for enhancement) | [LM Studio](https://lmstudio.ai), then enable the server in the Developer tab (port 1234) |
| A model | `lms get <model-identifier>`; see [operations.md](operations.md#local-llm-and-model-recommendations) |

The router runs without an LLM server. Enhancement and the orchestrator then return the original prompt (or fall back to OpenRouter if allowed; see [features.md](features.md#privacy-levels-and-cloud-fallback)).

## Install

```bash
cd <repo>/app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit; see the table below

cd ../mcps && npm install   # bridge dependencies
```

### Settings

All settings come from `app/.env` (see `app/.env.example` for the full annotated list).

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` / `PORT` | `0.0.0.0` / `9090` | Router bind address. Use `127.0.0.1` to reject LAN traffic |
| `LLM_HOST` / `LLM_PORT` | `localhost` / `1234` | Local LLM server (LM Studio or any OpenAI-compatible server, including Ollama) |
| `LLM_MODEL` | `qwen3-4b-instruct-2507` | Code-level default enhancement model; per-client models come from `enhancement-rules.json` |
| `LLM_ORCHESTRATOR_MODEL` | `qwen3-4b-thinking-2507` | Orchestrator model |
| `LLM_TIMEOUT` | `120` | LLM request timeout, seconds |
| `DATA_DIR` | `~/.prompthub` | Databases, audit log, checksums |
| `CACHE_MAX_SIZE` / `CACHE_PERSISTENT` | `1000` / `true` | L1 size; L2 SQLite write-through |
| `CB_FAILURE_THRESHOLD` / `CB_RECOVERY_TIMEOUT` | see `.env.example` | Circuit breaker |
| `MCP_SERVERS_CONFIG`, `ENHANCEMENT_RULES_CONFIG`, `API_KEYS_CONFIG` | `app/configs/*.json` | Config file overrides |
| `OPENROUTER_ENABLED`, `OPENROUTER_BASE_URL`, `OPENROUTER_TIMEOUT`, `OPENROUTER_DEFAULT_MODEL` | disabled | Cloud fallback |
| `LOG_LEVEL` | `info` | Logging |

`LLM_API_KEY` (alias `LM_API_TOKEN`) and other secrets are read from macOS Keychain via `app/scripts/manage-keys.py list`.

Config files in `app/configs/`:

| File | Purpose |
| --- | --- |
| `mcp-servers.json` | MCP server registry: command, args, env, `auto_start`, `restart_on_failure` |
| `enhancement-rules.json` | Per-client enhancement rules, `model_profiles`, `tool_profile`, privacy |
| `api-keys.json` | Bearer tokens for the `/v1/` API |
| `cloud-models.json` | Local model to free-tier cloud model mapping |

Servers with `auto_start: true` start with the router (`context7`, `desktop-commander`, `sequential-thinking`, `memory`, `duckduckgo`, `obsidian-mcp-tools`, `perplexity-comet`, `knowledge-to-action`). `chrome-devtools-mcp` is on-demand:

```bash
curl -X POST http://localhost:9090/servers/chrome-devtools-mcp/start
```

## Run the router

### Development

```bash
cd <repo>/app
source .venv/bin/activate
uvicorn router.main:app --host 127.0.0.1 --port 9090 --reload
```

### Helper scripts

```bash
app/scripts/prompthub-start.zsh   # checks the LLM server, starts uvicorn, waits for /health
app/scripts/prompthub-kill.zsh    # stops uvicorn and the bridge
```

`prompthub-start.zsh` assumes the repo lives at `$HOME/prompthub`; edit `ROOT` at the top if it lives elsewhere.

### LaunchAgent (daemon)

Create `~/Library/LaunchAgents/com.prompthub.router.plist` with the venv `uvicorn` as the program, `router.main:app --host 127.0.0.1 --port 9090` as arguments, `<repo>/app` as `WorkingDirectory`, `RunAtLoad` and `KeepAlive` true, and `StandardOutPath` / `StandardErrorPath` pointing at your log directory. Then:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.prompthub.router.plist
launchctl kickstart -k gui/$(id -u)/com.prompthub.router     # restart
launchctl bootout gui/$(id -u)/com.prompthub.router          # stop and unload
tail -f <log-dir>/router-stderr.log
```

Remove `--reload` in the daemon definition if you do not want restarts on file change.

## Verify

```bash
curl http://localhost:9090/health          # {"status":"healthy","services":{"router":"up","llm":"up",...},"servers":{...}}
curl http://localhost:9090/servers         # MCP servers and their state
open http://localhost:9090/dashboard       # servers, cache, circuit breakers, LLM, memory, tool registry
app/scripts/diagnose.sh                    # node, bridge, router, servers, client configs
```

`"llm":"down"` means the router cannot reach the LLM server; the router itself is fine. Tests: `cd app && pytest tests/ -v`.

## API tokens

Bearer tokens protect the OpenAI-compatible `/v1/` API only. They live in `app/configs/api-keys.json` (path override: `API_KEYS_CONFIG`):

```json
{
  "keys": {
    "sk-prompthub-<client>-001": {
      "client_name": "<client>",
      "enhance": false,
      "description": "what this key is for"
    }
  }
}
```

- `client_name` selects the enhancement rule and model profile.
- `enhance` turns enhancement on for requests made with this key. The client rule in `enhancement-rules.json` must also have `enabled: true` (see [features.md](features.md#prompt-enhancement)).
- Reload without restarting: `curl -X POST http://localhost:9090/v1/api-keys/reload` (admin endpoint, no auth; also a dashboard action).
- Do not commit real tokens. Keep secrets in Keychain (`app/scripts/manage-keys.py`).

The MCP routes (`/mcp/...`, `/mcp-direct/mcp`) and the bridge do not use these tokens.

## Connecting clients

Every client uses the same pattern. No per-client setup scripts exist; paste the config below into the client's MCP config.

1. Add the bridge as an MCP server (stdio).
2. Optionally point the client's model provider at `http://localhost:9090/v1` with a bearer token (see [features.md](features.md#openai-compatible-api)).

### The bridge entry

```json
{
  "command": "node",
  "args": ["<repo>/mcps/prompthub-bridge.js"],
  "env": {
    "PROMPTHUB_URL": "http://127.0.0.1:9090",
    "CLIENT_NAME": "<client-name>"
  }
}
```

`CLIENT_NAME` must match a client in `app/configs/enhancement-rules.json` (`claude-desktop`, `claude-code`, `codex`, `vscode`, `raycast`, `perplexity`, `cursor`, `comfyui`, `open-webui`, `lm-studio`, `opencode`). The router resolves that client's tool and model profiles server-side:

```bash
curl http://localhost:9090/clients/claude-code/tool-profile    # {disclosure, tier1_servers, source}
curl http://localhost:9090/clients/claude-code/model-profile   # {model_profile, resolved_model, source}
```

Optional bridge env vars (set in the same `env` block):

| Variable | Effect |
| --- | --- |
| `TOOL_DISCLOSURE`, `TIER1_SERVERS` | Pin progressive/full mode instead of using the router profile ([features.md](features.md#progressive-tool-disclosure)) |
| `SERVERS` | Comma-separated allowlist of servers to expose |
| `EXCLUDE_TOOLS` | Comma-separated prefixed tool names to hide, e.g. `desktop-commander_get_config` |
| `MINIFY_SCHEMAS` | `false` disables stripping of verbose `inputSchema` fields (on by default) |
| `DESC_MAX_LENGTH` | Tool description cap (default 200) |
| `TOOL_PREFIX_ALIASES` | `server:displayPrefix:stripFromTool,...` |

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{ "mcpServers": { "prompthub": { "command": "node", "args": ["<repo>/mcps/prompthub-bridge.js"],
  "env": { "PROMPTHUB_URL": "http://127.0.0.1:9090", "CLIENT_NAME": "claude-desktop" } } } }
```

Quit and reopen Claude Desktop, then confirm the PromptHub tools appear.

### Claude Code

Project `.mcp.json` (key `mcpServers`), or `claude mcp add`:

```json
{ "mcpServers": { "prompthub": { "command": "node", "args": ["<repo>/mcps/prompthub-bridge.js"],
  "env": { "PROMPTHUB_URL": "http://127.0.0.1:9090", "CLIENT_NAME": "claude-code" } } } }
```

### VS Code

`.vscode/mcp.json` (key `servers`):

```json
{ "servers": { "prompthub": { "type": "stdio", "command": "node", "args": ["<repo>/mcps/prompthub-bridge.js"],
  "env": { "PROMPTHUB_URL": "http://127.0.0.1:9090", "CLIENT_NAME": "vscode" } } } }
```

### LM Studio

`~/.lmstudio/mcp.json`, same shape as Claude Desktop with `CLIENT_NAME` `lm-studio`.

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.prompthub]
command = "node"
args = ["<repo>/mcps/prompthub-bridge.js"]

[mcp_servers.prompthub.env]
PROMPTHUB_URL = "http://127.0.0.1:9090"
CLIENT_NAME = "codex"
```

### OpenCode, Cursor, Raycast, Perplexity, ComfyUI

Use the same bridge entry with the matching `CLIENT_NAME` in the client's MCP config. Raycast and other OpenAI-compatible apps connect through the `/v1/` API instead (base URL `http://localhost:9090/v1`).

### Streamable HTTP (no bridge)

Clients that speak MCP over HTTP can connect directly to `http://127.0.0.1:9090/mcp-direct/mcp`. Set `GATEWAY_SERVERS` in `app/.env` (comma-separated server names) to limit what the gateway exposes; empty means all servers. See [Open WebUI](features.md#open-webui).

### Verify a client

1. Fully restart the client.
2. Ask it to list tools, or call `curl http://localhost:9090/tools/stats`.
3. Watch `http://localhost:9090/dashboard` activity, or `curl "http://localhost:9090/audit/activity?client_id=<name>&limit=5"`.

If tools do not appear, see [operations.md](operations.md#troubleshooting).

## Launchctl token environment

GUI apps (VS Code, Codex, Finder or Dock launches) do not inherit your shell environment, so token variables such as `GITHUB_PAT_TOKEN` can be missing even though they work in Terminal. `app/scripts/system/launchctl-env-audit.sh` compares shell and Keychain-backed tokens with the GUI session's `launchctl` environment. It prints only the source, a prefix, the length, and a short digest, never the secret.

```bash
app/scripts/system/launchctl-env-audit.sh check                    # compare sources vs launchctl
app/scripts/system/launchctl-env-audit.sh sync                     # push tokens into the GUI session
app/scripts/system/launchctl-env-audit.sh unset GITHUB_PAT_TOKEN   # clear a bad value, then run check
```

After `sync`, fully quit and relaunch the affected app.

- Editing shell startup files does not update running GUI apps.
- Restarting the router does not refresh a client's environment.
- `launchctl` values outlive the shell that set them.
- Token names differ by tool: Codex MCP tools expect `GITHUB_PAT_TOKEN`; Claude Code commonly uses `GITHUB_PERSONAL_ACCESS_TOKEN`.
