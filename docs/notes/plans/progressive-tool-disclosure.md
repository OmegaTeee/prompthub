# Plan: Progressive Tool Disclosure

> **Status:** Draft
> **Date:** 2026-04-05
> **Inspired by:** MCPGateway's lazy-loading approach (85% context reduction)
> **Affects:** `mcps/prompthub-bridge.js`, `app/configs/enhancement-rules.json`, dashboard

## Problem

The bridge currently dumps every tool from every running server into a
single `tools/list` response. With 9 servers and ~100+ tools, that's
~25 KB post-minification (~7K tokens) injected into every conversation's
context window before the user types a word.

Most conversations use 2-3 tools from 1-2 servers. The rest is dead weight.

## Goal

Reduce initial tool context by ~80-90% while keeping every tool
reachable within the same session. No tool should become permanently
inaccessible — just deferred until needed.

## Constraints

1. **MCP protocol rule:** Clients only allow the LLM to call tools
   returned by the most recent `tools/list` response. Hidden tools
   cannot be called — they must be promoted first.
2. **No client patches:** We can't modify Claude Desktop, VS Code, etc.
   The solution must work within standard MCP stdio transport.
3. **Backward-compatible:** `TOOL_DISCLOSURE=full` (current behavior)
   must remain the default. Progressive mode is opt-in per client.
4. **Per-client profiles:** PromptHub already customises enhancement
   per client. Tool profiles should follow the same pattern.

## Design

### Two-tier tool sets

```
Tier 1 — "always loaded"
  Tools returned on every tools/list call.
  Configured per client (see "Tool profiles" below).
  Includes the discover_tools meta-tool.

Tier 2 — "on demand"
  Tools NOT returned until the LLM explicitly loads them
  via the discover_tools or load_server_tools meta-tools.
```

### Meta-tools (registered by the bridge, not proxied to any server)

#### `discover_tools`

Returns a lightweight catalog of ALL available tools across all running
servers. Output is a table: server name, tool name, one-line description.
No schemas. This is what the LLM reads to decide what to load.

```
Input:  { server?: string, query?: string }
Output: text table or JSON list of { server, tool, description }
```

- `server` filter: show only tools from one server
- `query` filter: substring match on tool name or description
- No filter: full catalog

Cost: ~1-2 KB regardless of tool count (names + one-liners only).

#### `load_server_tools`

Promotes all tools from a specified server into the active tool set.
After this call, the next `tools/list` will include them, and the LLM
can call them directly.

```
Input:  { server: string }
Output: confirmation + count of tools loaded
```

Internally, the bridge adds the server to a session-level `activeServers`
set and triggers a `notifications/tools/list_changed` notification to
make the client re-fetch `tools/list`. (Claude Desktop and most MCP
clients honor this notification.)

### Session state (bridge-side)

```javascript
// Per-session state (reset on bridge restart / client reconnect)
let activeServers = new Set();   // servers whose tools are in tools/list
let tierOneServers = [];         // from config, always in activeServers

// On tools/list:
//   return tools from (tierOneServers union activeServers) + meta-tools

// On load_server_tools({ server: "obsidian-mcp-tools" }):
//   activeServers.add("obsidian-mcp-tools")
//   server.notification({ method: "notifications/tools/list_changed" })
```

### Tool profiles (per-client configuration)

Extend `enhancement-rules.json` (or a new `tool-profiles.json`) with
per-client tier-1 server lists:

```jsonc
// Option A: extend enhancement-rules.json
{
  "clients": {
    "claude-desktop": {
      // ... existing enhancement fields ...
      "tool_profile": {
        "disclosure": "progressive",
        "tier1_servers": ["desktop-commander", "sequential-thinking", "memory"]
      }
    },
    "claude-code": {
      "tool_profile": {
        "disclosure": "progressive",
        "tier1_servers": ["desktop-commander", "context7"]
      }
    },
    "cherry-studio": {
      "tool_profile": {
        "disclosure": "full"  // no change for this client
      }
    }
  }
}
```

The bridge reads CLIENT_NAME (already available as an env var) and loads
the matching profile. Default: `"disclosure": "full"` (backward compat).

### How tool profiles reach the bridge

Two options, in order of preference:

**Option A — Bridge fetches profile from router at startup.**
New endpoint: `GET /clients/{name}/tool-profile`. The bridge already
calls `GET /servers` at startup; one more fetch is trivial. This keeps
config centralized in the router.

**Option B — Env vars.**
`TIER1_SERVERS=desktop-commander,context7` alongside existing
`CLIENT_NAME` and `SERVERS`. Simpler but duplicates config per client.

Recommend Option A.

## Token budget estimate

| Scenario | tools/list size | Tokens (~4 chars/tok) |
|---|---|---|
| Current (full, minified) | ~25 KB | ~7,000 |
| Progressive (3 tier-1 servers, ~30 tools) | ~6 KB | ~1,700 |
| discover_tools catalog (9 servers, ~100 tools) | ~2 KB | ~550 |
| After load_server_tools (1 more server) | ~9 KB | ~2,500 |

**Typical session savings: ~70-75% of tool context never loaded.**

## Implementation phases

### Phase 1 — Meta-tools in the bridge (minimal, shippable)

1. Add `discover_tools` meta-tool to `prompthub-bridge.js`
   - Fetches full tool list internally (existing `getAllTools()`)
   - Returns only `{ server, name, description }` — no schemas
   - Registered alongside real tools in `tools/list`, always present
2. Add `load_server_tools` meta-tool
   - Maintains `activeServers` set in bridge memory
   - Sends `notifications/tools/list_changed` after mutation
3. Add `TOOL_DISCLOSURE` env var (`full` | `progressive`)
   - `full`: current behavior (meta-tools still available but inert)
   - `progressive`: `tools/list` only returns tier-1 + meta-tools
4. `TIER1_SERVERS` env var for initial testing (Option B above)

**No router changes needed.** The bridge already has all the data.

### Phase 2 — Per-client profiles via router

1. Add `tool_profile` field to enhancement-rules.json schema
2. New endpoint: `GET /clients/{name}/tool-profile`
3. Bridge fetches profile at startup instead of using env vars
4. Dashboard shows per-client disclosure mode and active tool counts

### Phase 3 — Smart tier-1 selection (optional, data-driven)

Use the tool registry's `serve_count` data to auto-promote frequently
used tools to tier 1. The registry already tracks this per-server:

```sql
SELECT server_name, serve_count FROM tool_cache ORDER BY serve_count DESC;
```

A nightly job (or dashboard button) could regenerate tier-1 lists from
actual usage patterns.

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Client ignores `list_changed` notification | Medium | Fallback: `discover_tools` returns schemas directly (defeats purpose but doesn't break). Test with each client before enabling. |
| LLM doesn't call `discover_tools` when needed | Low | Tier-1 covers common tools. Enhancement system prompts can hint: "Use discover_tools to find specialized tools." |
| Extra round-trip latency (discover → load → call) | Certain | Only affects first use of a tier-2 tool. Tier-1 tools have zero overhead. Catalog is cached in bridge memory. |
| Config drift between tool profiles and server roster | Low | Phase 2 centralizes in router. Phase 1 uses env vars which are adjacent to SERVERS filter. |

## Verification

- [ ] `TOOL_DISCLOSURE=full` behaves identically to current bridge
- [ ] `TOOL_DISCLOSURE=progressive` returns only tier-1 tools + 2 meta-tools
- [ ] `discover_tools` returns complete catalog for all running servers
- [ ] `discover_tools({ server: "X" })` filters correctly
- [ ] `load_server_tools({ server: "X" })` adds tools to next `tools/list`
- [ ] `notifications/tools/list_changed` triggers re-fetch in Claude Desktop
- [ ] Token count of progressive `tools/list` is <2 KB for 3 tier-1 servers

## Open questions

1. **Should `load_server_tools` support loading individual tools** (not
   whole servers)? This adds complexity but is more granular. Defer to
   Phase 3 unless there's a clear use case.
2. **Should the catalog include tool count per server?** Helps the LLM
   decide whether loading a server is worth it. Low cost to add.
3. **Does Cherry Studio / LM Studio honor `list_changed`?** Need to test.
   If not, those clients stay on `disclosure: full`.
