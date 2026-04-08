# servers/ Module

MCP server lifecycle management via FastMCP.

## Overview

The `servers/` module manages the full lifecycle of MCP (Model Context Protocol) servers:
- Subprocess spawning and termination via FastMCP `Client` + `StdioTransport`
- Health monitoring and auto-restart
- FastMCPBridge adapter for JSON-RPC dispatch
- Configuration and state management

## Architecture

```
┌──────────────┐
│  Supervisor  │  Orchestrates server lifecycle
└──────┬───────┘
       │
   ┌───▼────┐
   │Registry│  Configuration + state tracking
   └───┬────┘
       │
  ┌────▼──────────┐
  │FastMCPBridge  │  Typed dispatch via FastMCP Client
  └───────┬───────┘
          │
  ┌───────▼────────┐
  │StdioTransport  │  Subprocess lifecycle (FastMCP)
  └────────────────┘
```

## Components

### ServerRegistry
**File**: `servers/registry.py`

Central registry for MCP server configurations and state.

```python
class ServerRegistry:
    """
    Registry for MCP server configurations.

    Loads from JSON config file, provides CRUD operations,
    tracks process state.
    """

    def load(self) -> None:
        """Load servers from configs/mcp-servers.json"""

    def get(self, name: str) -> ServerConfig | None:
        """Get server configuration by name"""

    def add(self, config: ServerConfig) -> None:
        """Add new server configuration"""

    def remove(self, name: str) -> None:
        """Remove server configuration"""

    def get_auto_start_servers(self) -> list[ServerConfig]:
        """Get servers configured with auto_start=true"""
```

**Key Responsibilities**:
- Load/save server configurations from JSON
- Validate server configs with Pydantic
- Track process information (pid, status, restart count)
- Provide query interface for server state

**Data Models**:
```python
class ServerConfig(BaseModel):
    name: str                    # e.g., "context7"
    package: str                 # e.g., "@upstash/context7-mcp"
    transport: ServerTransport   # STDIO, HTTP
    command: str                 # e.g., "npx"
    args: list[str]              # e.g., ["-y", "@upstash/..."]
    env: dict[str, str | dict]   # Supports keyring references
    auto_start: bool = False
    restart_on_failure: bool = True
    max_restarts: int = 3
    description: str = ""

class ProcessInfo(BaseModel):
    status: ServerStatus         # STOPPED, STARTING, RUNNING, FAILED
    pid: int | None = None
    restart_count: int = 0
    last_error: str | None = None
```

### FastMCPBridge
**File**: `servers/fastmcp_bridge.py`

Adapter bridging PromptHub's JSON-RPC proxy to FastMCP's typed Client API.

```python
class FastMCPBridge:
    """
    Bridges HTTP JSON-RPC to MCP servers via FastMCP Client.

    Owns its subprocess lifecycle (spawn on start, kill on close)
    via FastMCP's StdioTransport.
    """

    def __init__(
        self,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        name: str = "unknown",
    ):
        """Create bridge with command/args/env — subprocess spawned on start()."""

    async def start(self) -> None:
        """Connect to MCP server (spawns subprocess + protocol handshake)."""

    async def close(self) -> None:
        """Disconnect and cleanup subprocess."""

    async def send(
        self,
        method: str,
        params: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Send JSON-RPC request — dispatches to typed FastMCP methods."""

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server."""

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server."""

    @property
    def is_connected(self) -> bool:
        """Check if the client is currently connected."""

    async def ping(self) -> bool:
        """Send a ping to verify the server is responsive."""
```

**Key Responsibilities**:
- Own subprocess lifecycle via FastMCP `StdioTransport`
- Dispatch JSON-RPC method names to typed FastMCP `Client` methods
- Wrap results in JSON-RPC envelope format for proxy compatibility
- Provide health check interface (`is_connected`, `ping()`)

**Dispatch Table**:

| JSON-RPC Method | FastMCP Client Method |
|---|---|
| `tools/list` | `client.list_tools_mcp()` |
| `tools/call` | `client.call_tool_mcp(name, arguments)` |
| `resources/list` | `client.list_resources_mcp()` |
| `resources/read` | `client.read_resource_mcp(uri)` |
| `prompts/list` | `client.list_prompts_mcp()` |
| `prompts/get` | `client.get_prompt_mcp(name, arguments)` |
| `initialize` | No-op (handled on connect) |
| `ping` | `client.ping()` |

### Supervisor
**File**: `servers/supervisor.py`

High-level orchestration: auto-start, health checks, restart on failure.

```python
class Supervisor:
    """
    Monitors server health and handles auto-restart.

    Runs background task to periodically check server health,
    restarts crashed servers (if configured), manages FastMCP bridges.
    """

    def __init__(self, registry: ServerRegistry, check_interval: float = 10.0):
        """Create supervisor with registry (no ProcessManager needed)."""

    async def start(self) -> None:
        """Start supervisor (auto-start servers + health check loop)"""

    async def stop(self) -> None:
        """Stop supervisor and all servers"""

    async def start_server(self, name: str) -> None:
        """Start server: resolve env, create FastMCPBridge, connect"""

    async def stop_server(self, name: str) -> None:
        """Stop server: close bridge, update registry"""

    async def restart_server(self, name: str) -> None:
        """Restart server"""

    def get_bridge(self, name: str) -> FastMCPBridge | None:
        """Get FastMCP bridge for server"""

    def get_status_summary(self) -> dict:
        """Get counts: running, stopped, failed"""
```

**Key Responsibilities**:
- Auto-start servers on application startup
- Periodic health checks (default: every 10 seconds)
- Detect disconnected servers via `bridge.is_connected`
- Auto-restart (if `restart_on_failure=true`)
- Respect `max_restarts` limit
- Create FastMCPBridge with keyring-resolved env vars
- Credential resolution via `resolve_server_env()` helper

**Health Check Flow**:
```
1. Timer fires (every 10s)
2. Iterate registered servers with RUNNING status
3. For each server:
   a. Check bridge.is_connected
   b. If disconnected AND restart_on_failure:
      - Increment restart_count
      - If restart_count <= max_restarts:
        → Close old bridge, restart server
      - Else:
        → Mark as FAILED
   c. If disconnected AND NOT restart_on_failure:
      → Mark as STOPPED
4. Log status changes
```

**Keyring Resolution**:
```python
def resolve_server_env(config: ServerConfig) -> dict[str, str]:
    """Resolve env vars, replacing keyring references with secrets."""
    # {"API_KEY": {"source": "keyring", "service": "prompthub", "account": "api_key"}}
    # → {"API_KEY": "<actual-secret-from-keychain>"}
```

## Usage Examples

### Start All Auto-Start Servers
```python
registry = ServerRegistry("configs/mcp-servers.json")
registry.load()

supervisor = Supervisor(registry)
await supervisor.start()  # Auto-starts configured servers
```

### Start Server Manually
```python
await supervisor.start_server("context7")

# Get bridge
bridge = supervisor.get_bridge("context7")

# Call tool
response = await bridge.call_tool(
    "query-docs",
    {"library": "fastapi", "query": "authentication"}
)
```

### Monitor Server Health
```python
# Get status summary
summary = supervisor.get_status_summary()
# {"running": 5, "stopped": 2, "failed": 0}

# Get specific server state
state = registry.get_state("context7")
print(f"Status: {state.process.status}")
print(f"Restart count: {state.process.restart_count}")

# Check bridge connectivity
bridge = supervisor.get_bridge("context7")
print(f"Connected: {bridge.is_connected}")
print(f"Responsive: {await bridge.ping()}")
```

### Graceful Shutdown
```python
await supervisor.stop()  # Closes all bridges and subprocesses
```

## Configuration

### mcp-servers.json
```json
{
  "servers": [
    {
      "name": "context7",
      "package": "@upstash/context7-mcp",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "auto_start": true,
      "restart_on_failure": true,
      "max_restarts": 3,
      "description": "Documentation fetching"
    }
  ]
}
```

### Environment with Keyring References
```json
{
  "name": "obsidian",
  "command": "npx",
  "args": ["-y", "mcp-obsidian"],
  "env": {
    "OBSIDIAN_API_KEY": {
      "source": "keyring",
      "service": "prompthub",
      "account": "obsidian_api_key"
    }
  }
}
```

## Testing

### Unit Tests
```python
# Test registry
def test_registry_load():
    registry = ServerRegistry("test-config.json")
    registry.load()
    assert "context7" in registry._servers

# Test bridge dispatch
@pytest.mark.asyncio
async def test_bridge_send():
    bridge = FastMCPBridge("npx", ["-y", "some-mcp"], name="test")
    await bridge.start()
    response = await bridge.send("tools/list")
    assert "result" in response
    await bridge.close()
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_server_lifecycle():
    supervisor = Supervisor(registry)
    await supervisor.start_server("context7")

    # Server running
    state = registry.get_state("context7")
    assert state.process.status == ServerStatus.RUNNING

    # Can call tools
    bridge = supervisor.get_bridge("context7")
    tools = await bridge.list_tools()
    assert len(tools) > 0

    # Clean shutdown
    await supervisor.stop_server("context7")
    assert state.process.status == ServerStatus.STOPPED
```

## Performance

### Metrics
- **Startup time**: 50-200ms per server (Node.js process spawn via StdioTransport)
- **Request latency**: 10-50ms (stdio roundtrip via FastMCP Client)
- **Memory**: 10-50MB per server process
- **Health check overhead**: <1ms (`is_connected` property check)

### Optimization
- Lazy start (auto_start=false for rarely used servers)
- Bridge reuse (FastMCPBridge maintains persistent connection)
- Batch health checks (check all servers in parallel)

## Troubleshooting

### Server Won't Start
```bash
# Check logs
tail -f ~/.prompthub/audit.log

# Check if command exists
which npx

# Test command manually
npx -y @upstash/context7-mcp
```

### Server Keeps Crashing
```python
# Check restart count
state = registry.get_state("context7")
print(state.process.restart_count)  # Max 3

# Check error logs
print(state.process.last_error)

# Reset restart count
await supervisor.stop_server("context7")  # Resets count
await supervisor.start_server("context7")
```

### Bridge Timeout
```python
# Increase timeout
response = await bridge.send(
    method="tools/call",
    params={...},
    timeout=60.0  # Default 30s
)
```

### Bridge Disconnected
```python
# Check connection state
bridge = supervisor.get_bridge("context7")
if not bridge.is_connected:
    # Supervisor will auto-restart if configured
    # Or manually restart:
    await supervisor.restart_server("context7")
```

## Related

- [ADR-001: Stdio Transport](../architecture/ADR-001-stdio-transport.md)
- [MCP Specification](https://modelcontextprotocol.io/docs/specification)
- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCPBridge Source](../../app/router/servers/fastmcp_bridge.py)
- [Supervisor Source](../../app/router/servers/supervisor.py)
