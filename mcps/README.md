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

## Server Roster (8 servers)

### Auto-start (7 servers)

Started automatically when the router boots. Restarted on failure up to 3 times.

| Server | Package | Transport | Description |
| --- | --- | --- | --- |
| context7 | `@upstash/context7-mcp` | stdio | Documentation fetching from libraries |
| desktop-commander | `@wonderwhy-er/desktop-commander` | stdio | File operations and terminal commands |
| sequential-thinking | `@modelcontextprotocol/server-sequential-thinking` | stdio | Step-by-step reasoning and planning |
| memory | `@modelcontextprotocol/server-memory` | stdio | Cross-session context persistence |
| duckduckgo | `ddg-mcp-search` | stdio | DuckDuckGo web search with SafeSearch and region support |
| perplexity-comet | `perplexity-comet-mcp` | stdio | Perplexity research via Comet browser CDP bridge |

### On-demand (1 server)

Started manually via `POST /servers/{name}/start` or dashboard. Set `auto_start: false`.

| Server | Package | Transport | Description |
| --- | --- | --- | --- |
| chrome-devtools-mcp | `chrome-devtools-mcp` | stdio | Chrome DevTools Protocol debugging and browser automation |


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
| `TOOL_DISCLOSURE` | `full` | `full` (all running servers' tools) or `progressive` (tier-1 + on-demand). See [Progressive tool disclosure](#progressive-tool-disclosure). |
| `TIER1_SERVERS` | (none) | Comma-separated servers seeded into the active set when `TOOL_DISCLOSURE=progressive` |

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
| `discover_tools` | Returns a lightweight catalog (`{server, tool, description}`) across running servers — no parameter schemas. Optional `server` and `query` filters. Used to find a tool before loading it in progressive mode. |
| `load_server_tools` | Promotes a server's tools into the active set and sends `notifications/tools/list_changed`. No-op effect in `full` mode (everything is already active). |

Use `prompthub_list_available_servers` to discover what exists, then call `prompthub_start_server` with the chosen name. The new server's tools appear in the next `tools/list` response. Use `prompthub_memory_search` to retrieve previously stored facts before answering. In `progressive` mode, use `discover_tools` to find a hidden tool and `load_server_tools` to make it callable.

### Progressive tool disclosure

Controls how many tools the bridge exposes in `tools/list`. Default `full` preserves the historical behavior (every running server's tools). `progressive` returns only tier-1 servers + the bridge meta-tools, then loads more on demand — cutting initial tool context by ~80% on a typical fleet.

**Modes:**

- `full` — `tools/list` returns every running server's tools plus all meta-tools.
- `progressive` — `tools/list` returns only servers in the active set (seeded from tier-1) plus meta-tools. The agent calls `discover_tools` to find a hidden tool, then `load_server_tools` to add its server to the active set; the bridge emits `notifications/tools/list_changed` so the client re-fetches.

**Configuration precedence** (highest first):

1. **Env vars** — `TOOL_DISCLOSURE` and/or `TIER1_SERVERS`. Setting *either one* pins the bridge to env-driven config and skips the router fetch entirely.
2. **Router profile** — only when *both* env vars are unset. The bridge fetches `GET /clients/{CLIENT_NAME}/tool-profile` at startup and uses its `disclosure` + `tier1_servers`. This keeps per-client config centralized in `enhancement-rules.json` (`tool_profile` block).
3. **Default** — `full`. Used when env is unset and the router is unreachable or has no profile for the client. Any error fetching the profile silently falls back here; the router never blocks bridge startup.

**Partial-env gotchas.** Because step 1 fires on *either* env var, two operator-friendly mistakes are worth knowing about:

- `TOOL_DISCLOSURE=progressive` alone → progressive mode, but `tier1Servers` is empty. `tools/list` returns only the bridge meta-tools and the agent has to `discover_tools` for everything. Valid as a "pure discovery" starting state; surprising if you expected tier-1 to come from the router.
- `TIER1_SERVERS=memory,context7` alone → `full` mode (the default). The active set is seeded, but `getEffectiveToolsList` ignores it in `full` mode, so the seeding has no effect.

The startup log line reflects what actually resolved, so a partial config is always visible there.

**Active-set rules:**

- The active set is seeded from tier-1 at startup and reset on every reconnect (it is per-session, not persisted).
- Tier-1 entries are intersected with *running* servers, so a stopped tier-1 server is silently skipped until it starts.
- `load_server_tools` validates the target is running and throws a clear error otherwise (no silent no-op).

**Startup log** confirms the resolved configuration:

```
Tool disclosure: progressive (tier1: memory, sequential-thinking, desktop-commander, source: router)
```

`source` is `env` or `router`, telling you which path won. End-user setup, tier-1 selection guidance, and verification chat examples live in [docs/guides/11-progressive-tool-disclosure.md](../docs/guides/11-progressive-tool-disclosure.md).

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

## Goose skills-mcp extension (lazy skill loading)

Goose loads the curated skill long-tail on demand via `skills-mcp` (configured in
[`clients/goose/config.yaml`](../clients/goose/config.yaml)) instead of eagerly injecting
the ~56K-token catalog that overflows local context. It exposes `list_skills` / `get_skill`
over two scopes: `~/.local/share/prompthub/skills-curated/` (56 skills) and `~/.claude/skills`.

Add a scope by appending another `-s <dir>` pair to the extension's `args`.

**Validated** (2026-06-17): the full chain works on Goose — `list_skills → get_skill → obey`
(an agent discovers a skill by purpose, loads only its body, and acts on it). The discover→load
directive lives in the global hint [`clients/goose/.goosehints`](../clients/goose/.goosehints)
(symlinked to `~/.config/goose/.goosehints`), so no per-prompt instruction is needed.

**Reliability caveat:** skill-routing depends on the model.
- Use an **instruct** model (`qwen3-4b-instruct-2507`) — it emits clean `tool_calls`. The
  **coder** model (`qwen3-coder-30b`) emits malformed `<function=…>` text and does **not** work.
- Load the model with **≥32K context** (the 96-skill `list_skills` result is large; 16K overflows).
- On a 4B model the hands-off chain is **flaky** (non-deterministic stalls at load). For reliable
  routing, add an explicit in-prompt directive, retry, or use a more capable model
  (`qwen3-8b` / a 27B distill). See `wiki/schema/qwen-local-writing-setup.md` in the LLM vault.

Deferred (separate work order): promoting `skills-mcp` into `prompthub-bridge.js` as a tier-1
meta-tool for cross-client serving (fills Cherry's empty Resources tab).

## References

- [Model Context Protocol](https://modelcontextprotocol.io) — official spec
- [MCP Servers Registry](https://github.com/modelcontextprotocol/servers) — official servers
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) — community list
