# MCP Servers

MCP servers managed by PromptHub. The router spawns, monitors, and auto-restarts these via [`app/configs/mcp-servers.json`](../app/configs/mcp-servers.json). Clients connect through the `prompthub-bridge.js` aggregator, which prefixes tool names by server and optionally minifies schemas.

## Structure

```text
mcps/
├── prompthub-bridge.js           Bridge aggregator (stdio → router → servers)
├── package.json                  npm dependencies for Node.js MCP servers
├── node_modules/                 Installed packages
└── README.md                     This file
```

## Server Roster (10 servers)

### Auto-start (7 servers)

Started automatically when the router boots. Restarted on failure up to 3 times.

| Server | Package | Transport | Description |
| --- | --- | --- | --- |
| context7 | `@upstash/context7-mcp` | stdio | Documentation fetching from libraries |
| desktop-commander | `@wonderwhy-er/desktop-commander` | stdio | File operations and terminal commands |
| sequential-thinking | `@modelcontextprotocol/server-sequential-thinking` | stdio | Step-by-step reasoning and planning |
| memory | `@modelcontextprotocol/server-memory` | stdio | Cross-session context persistence |
| duckduckgo | `ddg-mcp-search` | stdio | DuckDuckGo web search with SafeSearch and region support |
| obsidian-mcp-tools | standalone binary | stdio | Obsidian vault operations via MCP Tools plugin |
| perplexity-comet | `perplexity-comet-mcp` | stdio | Perplexity research via Comet browser CDP bridge |

### On-demand (3 servers)

Started manually via `POST /servers/{name}/start` or dashboard. Set `auto_start: false`.

| Server | Package | Transport | Description |
| --- | --- | --- | --- |
| obsidian | `mcp-obsidian` (pipx) | stdio | Obsidian vault file ops, batch reads, periodic notes, recent changes |
| chrome-devtools-mcp | `chrome-devtools-mcp` | stdio | Chrome DevTools Protocol debugging and browser automation |
| browsermcp | `@browsermcp/mcp` | stdio | Browser automation via Chrome extension WebSocket bridge |

### Standalone binaries (not npm-managed)

| Binary | Location | Installed via |
| --- | --- | --- |
| `mcp-server-fetch` | `~/.local/bin/mcp-server-fetch` | pipx (`mcp-server-fetch`) |
| `obsidian-mcp-tools` | `~/Vault/.obsidian/plugins/mcp-tools/bin/mcp-server` | Obsidian MCP Tools plugin |

`mcp-server-fetch` is referenced directly in client bridge configs (`.mcp.json`, `clients/*/mcp.json`) but is not in the router's `mcp-servers.json` — it runs independently alongside the bridge.

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
    "service": "prompthub",
    "key": "my_api_key"
  }
}
```

Then store the key: `python scripts/security/manage-keys.py set my_api_key`

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
