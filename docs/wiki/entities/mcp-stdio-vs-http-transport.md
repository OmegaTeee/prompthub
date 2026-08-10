---
slug: mcp-stdio-vs-http-transport
section: entities
status: documented
---
# MCP Stdio vs HTTP Transport

This entity explains the two prevailing transport mechanisms used by
MCP tools within PromptHub.

## Stdio
The MCP server runs as a child process; JSON‑RPC messages are exchanged
over its stdin/stdout (stderr carries logs).  No socket or network port
is involved.  This is fast and low‑overhead but couples the server to the
host that spawns it.

## HTTP
A streamable HTTP endpoint that carries JSON‑RPC over the network.  It’s
more flexible for remote operation and cross‑process access, and can be
fronted by bridge libraries like `mcp-remote`.  The HTTP variant suits
long‑lived services or when the server must run on a different host.

## Decision
PromptHub runs its MCP servers over **stdio** — every entry in
`app/configs/mcp-servers.json` uses `"transport": "stdio"`, spawned and
supervised by the Node.js bridge (`mcps/prompthub-bridge.js`).  HTTP is
reserved for the streamable gateway (`/mcp-direct/mcp`) and remote cases,
not the default for user‑facing servers.

## Related
- [[mcp-remote]] – HTTP bridge for the stdio binary.
- [[obsidian-local-rest-api]] – HTTP‑based MCP integration in a
  plugin.
