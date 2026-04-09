# MCP Transport Adapters

PromptHub connects desktop clients to MCP servers through three transport adapters, each bridging a different protocol boundary.

## Overview

Desktop MCP clients speak **stdio** — they spawn a subprocess and communicate via stdin/stdout JSON-RPC. PromptHub's router is an **HTTP** service managing multiple MCP servers. The adapters translate between these worlds:

```
┌──────────────────┐    stdio     ┌──────────────────┐    HTTP      ┌──────────────────┐    stdio     ┌──────────────┐
│  Desktop Client  │────────────▶│  prompthub-bridge │────────────▶│  Router (:9090)  │────────────▶│  MCP Server  │
│  (Claude, etc.)  │◀────────────│  (Node.js)        │◀────────────│  (FastAPI)       │◀────────────│  (npx/node)  │
└──────────────────┘   JSON-RPC   └──────────────────┘   JSON-RPC   └──────────────────┘  FastMCP     └──────────────┘
```

Without the bridge, each client would need individual configs for every MCP server. The bridge collapses N servers into one entry in the client's config file.

## Transport Paths at a Glance

| Path | Adapter | Location | Clients | Protocol |
|------|---------|----------|---------|----------|
| 1 | Stdio Bridge | `mcps/prompthub-bridge.js` | Claude Desktop, VS Code, Cursor, Raycast | stdio ↔ HTTP |
| 2 | Streamable HTTP Gateway | `router/servers/mcp_gateway.py` | Open WebUI, custom integrations | HTTP ↔ stdio |
| 3 | Internal FastMCPBridge | `router/servers/fastmcp_bridge.py` | Router itself (proxy route) | Python ↔ subprocess stdio |

---

## 1. Stdio Bridge (`mcps/prompthub-bridge.js`)

For clients that only speak stdio (Claude Desktop, VS Code, Cursor, Raycast). The bridge is a standalone Node.js MCP server using `@modelcontextprotocol/sdk`.

### Request Flow

```
Client spawns bridge process
  ↓ stdio (stdin/stdout)
Bridge (Node.js MCP server)
  ↓ HTTP POST /mcp/{server}/tools/list  or  /mcp/{server}/tools/call
Router → CircuitBreaker → ToolRegistryCache → FastMCPBridge
  ↓ FastMCP Client + StdioTransport
MCP Server subprocess
```

### MCP Methods

| Method | Behavior |
|--------|----------|
| `tools/list` | Fetches running servers from `GET /servers`, then calls `POST /mcp/{server}/tools/call` with `method: tools/list` for each. Aggregates and returns all tools with server-prefixed names. |
| `tools/call` | Splits the prefixed tool name (`server_tool`) to find the target server, then proxies the call to `POST /mcp/{server}/tools/call`. |

### Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROMPTHUB_URL` | `http://127.0.0.1:9090` | Router endpoint (explicit IPv4 to avoid DNS/IPv6 issues) |
| `CLIENT_NAME` | `claude-desktop` | Identifies the client for per-client enhancement and logging |
| `SERVERS` | _(empty = all)_ | Comma-separated whitelist of servers to expose |
| `EXCLUDE_TOOLS` | _(empty)_ | Comma-separated prefixed tool names to hide |
| `MINIFY_SCHEMAS` | `true` | Strip verbose JSON Schema fields from tool definitions |
| `DESC_MAX_LENGTH` | `200` | Truncate tool descriptions (0 = no limit) |

### Tool Name Prefixing

Every tool is prefixed with its server name to prevent collisions across servers:

```
context7's "resolve-library-id"  →  "context7_resolve-library-id"
desktop-commander's "read_file"  →  "desktop-commander_read_file"
```

On `tools/call`, the bridge splits on the **first** underscore only — tool names may themselves contain underscores (e.g., `desktop-commander_read_file` → server `desktop-commander`, tool `read_file`).

### Schema Minification

The bridge strips verbose JSON Schema fields to reduce LLM context usage (~67% reduction, ~14K tokens saved).

**Stripped**: `description`, `title`, `examples`, `default`, `$comment`, `$defs`, `definitions`

**Preserved**: `type`, `properties`, `required`, `enum`, `const`, `items`, `oneOf`/`anyOf`/`allOf`, `format`, `pattern`, `minimum`/`maximum`, `minLength`/`maxLength`, `minItems`/`maxItems`, `additionalProperties`

Minification is recursive — nested schemas in `properties`, `items`, and composition keywords are also stripped. Per-server savings are logged to stderr:

```
[minify] desktop-commander: 26 tools, 56910 → 13881 bytes (-76%)
[minify] context7: 2 tools, 1205 → 412 bytes (-66%)
```

### Client Config Generation

The CLI (`cli/generator.py`) and route (`router/clients/generators.py`) generate per-client bridge configs.

**Claude Desktop:**

```json
{
  "mcpServers": {
    "prompthub": {
      "command": "node",
      "args": ["/absolute/path/to/mcps/prompthub-bridge.js"],
      "env": {
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "CLIENT_NAME": "claude-desktop",
        "SERVERS": "context7,desktop-commander,sequential-thinking,memory,duckduckgo,obsidian-mcp-tools",
        "MINIFY_SCHEMAS": "true",
        "DESC_MAX_LENGTH": "200"
      }
    }
  }
}
```

**VS Code / Cursor:**

```json
{
  "mcp": {
    "servers": {
      "prompthub": {
        "command": "node",
        "args": ["/absolute/path/to/mcps/prompthub-bridge.js"],
        "env": { "CLIENT_NAME": "vscode", "..." : "..." }
      }
    }
  }
}
```

All paths are resolved to absolute at generation time. The CLI can generate (`generate`), install (`install`), validate (`validate`), and diff (`diff`) these configs.

### Graceful Shutdown

```javascript
process.stdout.on('error', () => process.exit(0));  // EPIPE on client exit
process.stdin.on('end', () => process.exit(0));      // stdin closed
```

---

## 2. Streamable HTTP Gateway (`/mcp-direct/mcp`)

For HTTP-native clients (Open WebUI, custom integrations) that can POST directly to the router without a stdio intermediary.

### Request Flow

```
Client sends HTTP POST
  ↓ HTTP POST /mcp-direct/mcp
FastMCP StreamableHTTPSessionManager
  ↓ FastMCPProxy per server
Dynamic client_factory() → resolve live bridge
  ↓ FastMCP Client + StdioTransport
MCP Server subprocess
```

### How It Works

The gateway in `router/servers/mcp_gateway.py` provides standards-compliant MCP over HTTP using FastMCP's `StreamableHTTPSessionManager`. It exposes the same servers as the stdio bridge but without the stdio translation layer.

Key design: **dynamic client factories**. Each server gets a `_make_client_factory()` that resolves the live bridge at request time. If a server restarts, the next request picks up the new bridge automatically.

Server filtering is controlled by the `GATEWAY_SERVERS` env var (comma-separated, empty = all). Topology changes (server install/delete) trigger a gateway rebuild via `_rebuild_gateway()`.

### When to Use

- Open WebUI connecting via `/v1/` proxy + `/mcp-direct/mcp`
- Custom HTTP integrations that don't need a stdio wrapper
- Reducing tool count for smaller models via `GATEWAY_SERVERS` filtering

---

## 3. Internal FastMCPBridge (`router/servers/fastmcp_bridge.py`)

The Python-side wrapper that both adapters ultimately use to communicate with MCP server subprocesses.

### How It Works

Wraps a FastMCP `Client` + `StdioTransport` pair:

```python
bridge = FastMCPBridge(command="npx", args=["-y", "@upstash/context7-mcp"], env={...})
await bridge.start()        # Spawns subprocess, performs MCP handshake
result = await bridge.send("tools/list", {})   # Dispatches to Client.list_tools_mcp()
await bridge.close()        # Kills subprocess
```

### Method Dispatch

| JSON-RPC Method | FastMCP Client Method |
|----------------|----------------------|
| `tools/list` | `list_tools_mcp()` |
| `tools/call` | `call_tool_mcp()` |
| `resources/list` | `list_resources_mcp()` |
| `resources/read` | `read_resource_mcp()` |
| `prompts/list` | `list_prompts_mcp()` |
| `prompts/get` | `get_prompt_mcp()` |

---

## Shared Infrastructure

### MCP Proxy Route (`/mcp/{server}/{path}`)

The proxy route in `router/routes/mcp_proxy.py` is the HTTP endpoint the stdio bridge calls. It adds resilience and caching layers:

```
Request arrives
  │
  ├─ Circuit breaker OPEN? → 503 with retry_after header
  │
  ├─ Server not running + auto_start? → Supervisor.start_server()
  │
  ├─ tools/list + cache hit? → Return cached (metadata: "cache": "hit")
  │
  ├─ bridge.send(method, params, timeout=30s)
  │   └─ FastMCP Client → StdioTransport → subprocess
  │
  ├─ tools/list + cache miss? → tool_registry.cache_tools() (SQLite, 24h TTL)
  │
  ├─ Record circuit breaker success/failure
  │
  └─ Return response with metadata (cache status, elapsed_ms, timeout_used)
```

### Tool Registry Cache-Through

`tools/list` responses are cached in SQLite (`~/.prompthub/tool_registry.db`):

- **Cache hit**: Return stored tools immediately, skip live fetch
- **Cache miss**: Proxy to live server, store result, return with `"cache": "miss"`
- **TTL**: 24 hours (configurable)
- **Archival**: Old snapshots auto-move to `tool_cache_archive` on upsert
- **Manual refresh**: `POST /tools/{server}/refresh` forces a live fetch

This means the bridge's `tools/list` call is fast on subsequent requests — no subprocess round-trip needed.

### Circuit Breaker

Each MCP server gets its own circuit breaker (3 failures → OPEN, 30s → HALF_OPEN, 1 success → CLOSED). The proxy route checks the breaker before proxying and records outcomes after:

```
CLOSED ──[3 failures]──▶ OPEN ──[30s timeout]──▶ HALF_OPEN
  ▲                                                  │
  └──────────────[1 success]─────────────────────────┘
```

When OPEN, the proxy returns `503 Service Unavailable` with a `retry_after` header — the bridge surfaces this as an MCP error to the client.

### Server Lifecycle

#### Server Registry (`router/servers/registry.py`)

Loads `configs/mcp-servers.json` and tracks config (persistent) and runtime state (ephemeral `ProcessInfo` with pid, status, restart count).

#### Supervisor (`router/servers/supervisor.py`)

Owns the lifecycle of all MCP servers:

1. **Boot**: Starts all servers with `auto_start: true`
2. **Health loop**: Every 10s, checks if processes are alive
3. **Auto-restart**: Restarts crashed servers up to `max_restarts` times
4. **Environment resolution**: Resolves `{"source": "keyring"}` env vars via macOS Keychain
5. **Bridge management**: Maintains `{server_name: FastMCPBridge}` dict

### Graceful Shutdown (Router)

The lifespan context manager ensures clean teardown:

1. Close gateway lifespan (exits FastMCP session manager)
2. Stop supervisor (closes all bridges, cancels health loop)
3. Close enhancement service and orchestrator
4. Flush persistent storage

Each `FastMCPBridge.close()` kills its subprocess.

## Error Handling

| Failure | Bridge behavior | Router behavior |
|---------|----------------|-----------------|
| Router unreachable | Logs error, uses cached server list | N/A |
| Server not running | Returns MCP error | Auto-starts if `auto_start: true` |
| Server crash | Returns MCP error | Supervisor auto-restarts (up to `max_restarts`) |
| Timeout (30s) | Returns MCP error | Circuit breaker records failure |
| Circuit breaker open | Returns MCP error | 503 with `retry_after` |
| Invalid tool name | Throws "Invalid tool name format" | N/A |

## Dependencies

### Bridge (`mcps/package.json`)

- `@modelcontextprotocol/sdk` — MCP server/transport implementation

### Router (`app/requirements.txt`)

- `fastmcp` — MCP client, StdioTransport, StreamableHTTPSessionManager, FastMCPProxy
- `fastapi` — HTTP framework
- `httpx` — Async HTTP client (for LM Studio, OpenRouter, and other HTTP backends)
- `aiosqlite` — Async SQLite (tool registry, activity log, memory)

## Related Documents

- [ADR-001: Stdio Transport](ADR-001-stdio-transport.md) — Why stdio is the primary transport
- [ADR-002: Circuit Breaker](ADR-002-circuit-breaker.md) — Resilience pattern details
- [ADR-004: Modular Monolith](ADR-004-modular-monolith.md) — Why a single FastAPI app
