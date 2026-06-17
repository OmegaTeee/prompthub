---
slug: mcp-stdio-vs-http-transport
section: entities
status: documented
---
# MCP Stdio vs HTTP Transport

This entity explains the two prevailing transport mechanisms used by
MCP tools within PromptHub.

## Stdio
A direct Unix domain socket or TCP connection to the Go binary.  The
client reads from stdout/stderr and writes to stdin.  This is fast
and has low overhead but requires a tightly coupled binary.

## HTTP
A REST‑style HTTP endpoint that forwards JSON RPC calls to the Go
binary.  It’s more flexible for remote operation and can be used
with webhooks or cross‑process bridge libraries like
`mcp-remote`.  The HTTP variant is chosen for long‑lived
services and when the binary must run on a different host.

## Decision
Prompthub has migrated from stdio to HTTP for most user‑facing
services, keeping stdio only for legacy tooling.

## Related
- [[mcp-remote]] – HTTP bridge for the stdio binary.
- [[obsidian-local-rest-api]] – HTTP‑based MCP integration in a
  plugin.
