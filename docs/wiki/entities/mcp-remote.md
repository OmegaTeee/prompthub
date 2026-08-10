---
slug: mcp-remote
section: entities
status: documented
---
# MCP Remote

The MCP Remote is a lightweight shim for communicating with a local
`mcp-tools` binary over a UNIX domain socket or TCP. It exposes a JSON
RPC interface where requests are marshalled with Go structs and the
response is streamed back to the caller.  The protocol is intentionally
simple: the client sends a JSON string containing the command name
and an array of arguments, the server replies with a JSON string
conveying the result or a 4‑byte error code.

## Use case
A Prompthub client (e.g. the OpenAI API wrapper) can spawn an
`mcp-tools` instance locally and then communicate over the
`mcp-remote` endpoint, thereby keeping the heavy Go binary
separate from the Python runtime.

## Related
- [[mcp-stdio-vs-http-transport]] – comparison of the two
  communication approaches.
- [[obsidian-local-rest-api]] – another plugin that ships an MCP
  server inside the process.
