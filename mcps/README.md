# MCP Servers

MCP servers managed by PromptHub. The router spawns, monitors, and auto-restarts these via [`app/configs/mcp-servers.json`](../app/configs/mcp-servers.json). Clients connect through the `prompthub-bridge.js` aggregator, which prefixes tool names by server and optionally minifies schemas.

- [`prompthub-bridge.js`](./prompthub-bridge.js) → Source Node.js bridge script that is the main entry point for all servers to clients via stdio.
- `~/.local/bin/mcp-bridge` → `$PATH` symlink to the bridge script

## Structure

```text
mcps/
├── prompthub-bridge.js           Bridge aggregator (stdio → router → servers)
├── package.json                  npm dependencies for Node.js MCP servers
├── node_modules/                 Installed packages
├── TOOL_USE.md                   Tool routing guidance for clients
└── README.md                     This file
```

## Server Roster (11 servers)

### Auto-start (7 servers)

Started automatically when the router boots. Restarted on failure up to 3 times.

| Server | Package | Transport | Description |
| --- | --- | --- | --- |
| context7 | `@upstash/context7-mcp` | stdio | Documentation fetching from libraries |
| desktop-commander | `@wonderwhy-er/desktop-commander` | stdio | File operations and terminal commands |
| sequential-thinking | `@modelcontextprotocol/server-sequential-thinking` | stdio | Step-by-step reasoning and planning |
| memory | `@modelcontextprotocol/server-memory` | stdio | Cross-session context persistence |
| duckduckgo | `ddg-mcp-search` | stdio | DuckDuckGo web search with SafeSearch and region support |
| obsidian-mcp-tools | `obsidian-mcp-tools` (binary `mcp-obsidian-vault`) | stdio | Obsidian vault operations via the MCP Tools plugin |
| perplexity-comet | `perplexity-comet-mcp` | stdio | Perplexity research via Comet browser CDP bridge |

### On-demand (4 servers)

Started manually via `POST /servers/{name}/start` or dashboard. Set `auto_start: false`.

| Server | Package | Transport | Description |
| --- | --- | --- | --- |
| chrome-devtools-mcp | `chrome-devtools-mcp` | stdio | Chrome DevTools Protocol debugging and browser automation |
| browsermcp | `@browsermcp/mcp` | stdio | Browser automation via Chrome extension WebSocket bridge |
| applescript-mcp | `@peakmojo/applescript-mcp` (global) | stdio | macOS automation via AppleScript |
| homebrew | (built-in: `brew mcp-server`) | stdio | Homebrew package management |

### Standalone binaries (not npm-managed)

| Binary | Location | Installed via |
| --- | --- | --- |
| `mcp-server-fetch` | `~/.local/bin/mcp-server-fetch` | pipx (`mcp-server-fetch`) |
| `mcp-obsidian-vault` | `~/.local/bin/mcp-obsidian-vault` | Obsidian plugin |


  **MCP_OBSIDIAN_VAULT** is a PATH symlink to Obsidian's MCP Tools plugin's standalone binary. This is the version used by the router since it has direct vault access for features like periodic notes and recent changes. Plugin must run from within Obsidian to access vault files. Used for Obsidian-specific operations like periodic notes and recent changes.
  - $MCP_OBSIDIAN_VAULT →
    - SYMLINK="~/.local/bin/mcp-obsidian-vault"
      - TARGET="~/Vault/.obsidian/plugins/mcp-tools/bin/mcp-server"

  <!--
  - `mcp-obsidian-pipx` → (~/.local/bin/mcp-obsidian-pipx) -> `~/.local/pipx/venvs/mcp-obsidian/bin/mcp-obsidian`
    - Separate build outside of plugins for testing. Used for testing and development of Obsidian MCP server without needing to run the full Obsidian app. Lacks vault access, so some features are limited.
  /-->

  **MCP_SERVER_FETCH** is a $PATH symlink to Standalone Python MCP server for fetching URLs with `requests`. Used for tools that need to fetch web content without CORS issues, like Claude's `fetch_url` tool. Not managed by the router since it's a standalone binary, but referenced directly in client bridge configs.
  - $PATH="mcp-server-fetch" →
    - SYMLINK="~/.local/bin/mcp-server-fetch"
      - TARGET="~/.local/pipx/venvs/mcp-server-fetch/bin/mcp-server-fetch"

Currently `mcp-server-fetch` is referenced directly in client bridge configs (`.mcp.json`, `clients/*/mcp.json`) but is not in the router's `mcp-servers.json` — it runs independently alongside the bridge.

## Bridge (`prompthub-bridge.js`)

The bridge is a stdio MCP server that aggregates tools from all router-managed servers into a single tool list for clients. Clients like Claude Code, LM Studio, and Raycast connect to the bridge, not to individual servers.

### How it works

1. Client starts `node prompthub-bridge.js` with env vars (`SERVERS`, `CLIENT_NAME`, etc.)
2. Bridge calls `GET /servers` on the router to discover available servers
3. For each server, bridge calls `POST /mcp/{server}/tools/list` to get tools
4. Tools are prefixed with server name: `memory_create_entities`, `context7_query-docs`
5. Schema minification strips verbose fields (~67% size reduction)
6. Client receives the aggregated, minified tool list via stdio

### Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `PROMPTHUB_URL` | `http://127.0.0.1:9090` | Router endpoint |
| `AUTHORIZATION` | — | Bearer token from `api-keys.json` |
| `CLIENT_NAME` | — | Client identifier for audit logging |
| `SERVERS` | (all) | Comma-separated server filter (e.g., `memory,context7,sequential-thinking`) |
| `MINIFY_SCHEMAS` | `true` | Strip `description`, `title`, `examples`, `default` from tool schemas |
| `DESC_MAX_LENGTH` | `200` | Truncate remaining descriptions to this length |

### Schema minification

Enabled by default. Reduces tool context from ~75 KB to ~25 KB (~14K tokens saved).

**Stripped**: `description`, `title`, `examples`, `default`, `$comment`, `$defs`
**Kept**: `type`, `properties`, `required`, `enum`, `items`, `oneOf/anyOf/allOf`, `format`, `pattern`, `min/max` constraints

Disable with `MINIFY_SCHEMAS=false` for debugging.

### Meta-tools

The bridge exposes synthetic tools that don't proxy to a backend MCP server. They let agents discover and start on-demand servers (`auto_start: false`) whose tools are otherwise invisible until the server is running, and search persistent session memory.

| Tool | Purpose |
| --- | --- |
| `prompthub_list_available_servers` | Calls `GET /servers`. Returns every configured server with status (`running`, `stopped`, `failed`). |
| `prompthub_start_server` | Calls `POST /servers/{name}/start`, polls `/servers` until the target reaches `running` status (15 s timeout), refreshes the bridge's server cache, then sends a `notifications/tools/list_changed` so MCP clients re-fetch tools. |
| `prompthub_memory_search` | Calls `POST /sessions/search`. BM25-ranked search over session facts and memory blocks (SQLite FTS5). Validates `limit` 1-100. Scoped to the caller's client ID by default; pass `cross_client: true` to opt out. |

Use `prompthub_list_available_servers` to discover what exists, then call `prompthub_start_server` with the chosen name. The new server's tools appear in the next `tools/list` response. Use `prompthub_memory_search` to retrieve previously stored facts before answering.

## Adding a new MCP server

### npm package

```bash
cd mcps
npm install <package-name>
```

Add to [`app/configs/mcp-servers.json`](../app/configs/mcp-servers.json):

```json
{
  "servers": {
    "<server-name>": {
      "package": "<package-name>",
      "transport": "stdio",
      "command": "node",
      "args": ["./mcps/node_modules/<package-name>/dist/index.js"],
      "env": {},
      "auto_start": false,
      "restart_on_failure": true,
      "max_restarts": 3,
      "health_check_interval": 30,
      "description": "What this server does"
    }
  }
}
```

If the server needs API keys, use the keyring pattern:

```json
"env": {
  "API_KEY": {
    "source": "keyring",
    "key": "my_api_key"
  }
}
```

The runtime resolves this to a Keychain entry at `service=prompthub:my_api_key`, `account=$USER`.

Then store the key (from `app/` with venv active): `python scripts/manage-keys.py set my_api_key`

### Standalone binary

Add directly to `mcp-servers.json` with the binary path as `command`. If it needs credentials, use the keyring env block pattern (see Obsidian entries in `mcp-servers.json` for example).

## Upgrading servers

```bash
cd mcps
npm update              # update all
npm update <package>    # update one
```

## Diagnostics

```bash
./scripts/diagnose.sh          # full stack check
curl localhost:9090/servers     # list servers and status
curl localhost:9090/tools/stats # tool registry cache stats
```

## References

- [Model Context Protocol](https://modelcontextprotocol.io) — official spec
- [MCP Servers Registry](https://github.com/modelcontextprotocol/servers) — official servers
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) — community list
