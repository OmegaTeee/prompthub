# ADR-001: Stdio Transport for MCP Servers

## Status
Accepted

## Context
MCP (Model Context Protocol) servers need a transport mechanism for communication with the router. Available options:

1. **Stdio** - JSON-RPC over stdin/stdout
2. **HTTP/SSE** - REST endpoints with Server-Sent Events
3. **WebSocket** - Bidirectional persistent connections
4. **gRPC** - Protocol buffers over HTTP/2

### Requirements
- Must support existing MCP server ecosystem (npm packages)
- Simple process lifecycle management (start/stop/restart)
- Low latency for request/response patterns
- Support for concurrent requests
- Easy debugging and testing

### MCP Ecosystem Reality
- 95% of MCP servers use stdio transport
- Official MCP SDKs default to stdio
- Most servers are npm packages designed for stdio

## Decision
Use **stdio transport** as the primary and default transport mechanism.

### Implementation Details
- Spawn MCP servers as subprocesses using `asyncio.subprocess`
- Communicate via newline-delimited JSON (NDJSON)
- Use `StdioBridge` to manage request/response matching
- Support concurrent requests via request ID correlation

## Rationale

### Pros
✅ **Ecosystem compatibility** - Works with all existing MCP servers
✅ **Simple lifecycle** - Standard process management (start/stop/restart)
✅ **Low overhead** - No network stack, direct IPC
✅ **Easy debugging** - Can pipe stdin/stdout to files for inspection
✅ **Security** - No exposed ports, local-only communication
✅ **Resource isolation** - Each server is a separate process with its own memory

### Cons
❌ **No remote servers** - Can't communicate with MCP servers on other machines
❌ **Process overhead** - Each server requires a separate process (~10-50MB)
❌ **Serialization overhead** - JSON parsing on every message
❌ **No streaming** - Request/response only, no bidirectional streams

## Consequences

### Positive
- Can use all MCP servers from npm ecosystem out of the box
- Simple codebase without network complexity
- Natural process isolation provides security boundaries
- Easy to monitor processes (pid, status, restart count)

### Negative
- Cannot scale horizontally (servers tied to local machine)
- Limited to local-only deployment
- Process spawning adds latency (~50-100ms on first request)

### Neutral
- Future WebSocket support requires new transport layer
- HTTP/SSE servers would need different bridge implementation

## Alternatives Considered

### HTTP/SSE Transport
**Rejected** because:
- Very few MCP servers support this (< 5% of ecosystem)
- Adds network complexity and latency
- Requires port management and conflict resolution
- Authentication/authorization complexity

**When to reconsider**: If remote MCP servers become a requirement

### WebSocket Transport
**Deferred to Phase 4** because:
- Not supported by current MCP ecosystem
- More complex protocol (connection lifecycle, ping/pong)
- Bidirectional streaming not needed for current use cases

**When to implement**: For real-time notifications, streaming responses, or remote servers

### gRPC Transport
**Rejected** because:
- No MCP servers use gRPC
- Protocol buffers require schema management
- Higher implementation complexity
- Not compatible with JSON-RPC ecosystem

## Implementation Notes

### StdioBridge Pattern

```python
# Spawn process
process = await asyncio.create_subprocess_exec(
    "npx", "-y", "@upstash/context7-mcp",
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)

# Create bridge
bridge = StdioBridge(process, "context7")
await bridge.start()

# Send request
response = await bridge.send("tools/list", {})
```

### Request ID Matching
- Router generates sequential request IDs
- Bridge stores pending futures in dict by request ID
- Background reader task matches responses to futures
- Timeout cleanup prevents memory leaks

### Error Handling
- Process crash → Supervisor detects and restarts
- Malformed JSON → Logged, response skipped
- Request timeout → Future cancelled, request cleaned up

## Metrics
- **Latency**: 10-50ms (process-to-process communication)
- **Throughput**: Limited by individual MCP server (typically ~100 req/s)
- **Memory**: 10-50MB per server process
- **CPU**: Negligible (IO-bound)

## Related
- [ADR-002: Circuit Breaker Pattern](ADR-002-circuit-breaker.md) - Handles stdio failures
- [ADR-004: Modular Monolith](ADR-004-modular-monolith.md) - Why local-only is acceptable

## References
- [MCP Stdio Transport Spec](https://modelcontextprotocol.io/docs/specification/transport#stdio)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Node.js stdio in Claude Desktop](https://github.com/anthropics/claude-desktop/blob/main/docs/mcp.md)

## Revision History
- 2025-01-15: Initial decision
- 2025-02-02: Documented as ADR
