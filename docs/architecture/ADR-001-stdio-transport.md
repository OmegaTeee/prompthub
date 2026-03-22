# ADR-001: Stdio Transport for MCP Servers

## Status
Accepted (Updated — implementation migrated to FastMCP, Feb 2026)

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
- Spawn MCP servers as subprocesses via FastMCP's `StdioTransport`
- Protocol handling (JSON-RPC framing, handshake) managed by FastMCP `Client`
- `FastMCPBridge` adapter class provides backward-compatible `send()` interface
- Typed dispatch: `tools/list` → `Client.list_tools_mcp()`, `tools/call` → `Client.call_tool_mcp()`, etc.

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

### FastMCPBridge Pattern (Current)

```python
from router.servers.fastmcp_bridge import FastMCPBridge

# Create bridge (owns its subprocess lifecycle)
bridge = FastMCPBridge(
    command="npx",
    args=["-y", "@upstash/context7-mcp"],
    env=resolved_env,
    name="context7",
)
await bridge.start()  # Spawns subprocess + MCP handshake

# Send request (dispatches to typed FastMCP Client methods)
response = await bridge.send("tools/list", {})

# Health check
if bridge.is_connected:
    await bridge.ping()
```

### Dispatch Model
- `FastMCPBridge.send()` routes by JSON-RPC method name to typed `Client` methods
- `_mcp` variants (`list_tools_mcp`, `call_tool_mcp`) return raw Pydantic models
- Results wrapped in JSON-RPC envelope: `{"jsonrpc": "2.0", "result": {...}, "id": 1}`
- No manual request ID matching — FastMCP handles framing internally

### Error Handling
- Process crash → `bridge.is_connected` returns False → Supervisor restarts
- Timeout → `asyncio.wait_for()` raises `TimeoutError`
- Bridge closed → `FastMCPBridgeError("Bridge is closed")` raised

### Historical: StdioBridge (Removed)
The original implementation used a custom `StdioBridge` class that managed
raw JSON-RPC over stdin/stdout with manual request ID matching. This was
replaced by `FastMCPBridge` in Feb 2026 to leverage FastMCP's built-in
protocol handling, reducing ~560 lines of custom bridge + process code.

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
- 2026-02-17: Migrated from custom StdioBridge to FastMCPBridge (fastmcp>=2.0.0)
