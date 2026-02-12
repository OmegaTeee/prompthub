# servers/ Module

MCP server lifecycle management and stdio communication.

## Overview

The `servers/` module manages the full lifecycle of MCP (Model Context Protocol) servers:
- Process spawning and termination
- Health monitoring and auto-restart
- Stdio bridge for JSON-RPC communication
- Configuration and state management

## Architecture

```
┌──────────────┐
│  Supervisor  │  Orchestrates server lifecycle
└──────┬───────┘
       │
   ┌───▼────┐  ┌────────────┐
   │Registry│  │ProcessMgr  │  Manages processes
   └───┬────┘  └──────┬─────┘
       │              │
       └────┬─────────┘
            │
      ┌─────▼──────┐
      │StdioBridge │  JSON-RPC over stdin/stdout
      └────────────┘
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
    transport: ServerTransport   # STDIO, SSE, HTTP
    command: str                 # e.g., "npx"
    args: list[str]              # e.g., ["-y", "@upstash/..."]
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

### ProcessManager
**File**: `servers/process.py`

Low-level process spawning and management.

```python
class ProcessManager:
    """
    Manages MCP server processes.

    Spawns processes using asyncio.subprocess, tracks PIDs,
    handles graceful shutdown.
    """

    async def start(self, name: str) -> None:
        """Start a server process"""

    async def stop(self, name: str, timeout: float = 5.0) -> None:
        """Stop a server process (SIGTERM then SIGKILL)"""

    async def restart(self, name: str) -> None:
        """Restart a server process"""

    def get_process(self, name: str) -> asyncio.subprocess.Process | None:
        """Get process handle by name"""

    def get_running_servers(self) -> list[str]:
        """List all running server names"""

    async def stop_all(self) -> None:
        """Stop all managed processes"""
```

**Key Responsibilities**:
- Spawn processes with `asyncio.create_subprocess_exec`
- Configure stdin/stdout/stderr pipes
- Track process handles by name
- Graceful shutdown (SIGTERM → wait → SIGKILL)
- Cleanup zombie processes

**Process Lifecycle**:
```
1. start() → asyncio.create_subprocess_exec
2. Configure pipes (stdin=PIPE, stdout=PIPE, stderr=PIPE)
3. Store process handle
4. Update registry with pid and status=RUNNING
5. stop() → SIGTERM → wait(5s) → SIGKILL if needed
6. Close pipes
7. Remove process handle
8. Update registry with status=STOPPED
```

### Supervisor
**File**: `servers/supervisor.py`

High-level orchestration: auto-start, health checks, restart on failure.

```python
class Supervisor:
    """
    Monitors server health and handles auto-restart.

    Runs background task to periodically check server health,
    restarts crashed servers (if configured), manages stdio bridges.
    """

    async def start(self) -> None:
        """Start supervisor (auto-start servers + health check loop)"""

    async def stop(self) -> None:
        """Stop supervisor and all servers"""

    async def start_server(self, name: str) -> None:
        """Start server and initialize bridge"""

    async def stop_server(self, name: str) -> None:
        """Stop server and close bridge"""

    async def restart_server(self, name: str) -> None:
        """Restart server"""

    def get_bridge(self, name: str) -> StdioBridge | None:
        """Get stdio bridge for server"""

    def get_status_summary(self) -> dict:
        """Get counts: running, stopped, failed"""
```

**Key Responsibilities**:
- Auto-start servers on application startup
- Periodic health checks (default: every 10 seconds)
- Detect crashed processes
- Auto-restart (if `restart_on_failure=true`)
- Respect `max_restarts` limit
- Create and manage stdio bridges
- Initialize MCP protocol handshake

**Health Check Flow**:
```
1. Timer fires (every 10s)
2. Get list of running servers
3. For each server:
   a. Check if process is alive (process.returncode)
   b. If dead AND restart_on_failure:
      - Increment restart_count
      - If restart_count <= max_restarts:
        → Restart server
      - Else:
        → Mark as FAILED
   c. If dead AND NOT restart_on_failure:
      → Mark as STOPPED
4. Log status changes
```

### StdioBridge
**File**: `servers/bridge.py`

JSON-RPC communication over stdin/stdout.

```python
class StdioBridge:
    """
    Bridges HTTP JSON-RPC to stdio JSON-RPC.

    Manages async read/write to subprocess stdin/stdout,
    matches responses to requests by request ID.
    """

    async def start(self) -> None:
        """Start background reader task"""

    async def close(self) -> None:
        """Close bridge and cancel pending requests"""

    async def send(
        self,
        method: str,
        params: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Send JSON-RPC request and wait for response"""

    async def send_notification(
        self,
        method: str,
        params: dict | None = None,
    ) -> None:
        """Send JSON-RPC notification (no response)"""

    async def initialize(self) -> dict:
        """Send MCP initialize request"""

    async def list_tools(self) -> list[dict]:
        """List available tools from server"""

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a tool on the server"""
```

**Key Responsibilities**:
- Serialize JSON-RPC requests to NDJSON (newline-delimited JSON)
- Write to process stdin
- Read from process stdout in background task
- Parse NDJSON responses
- Match responses to requests by `id` field
- Handle timeouts and errors
- MCP protocol handshake (`initialize`, `initialized`)

**Request Flow**:
```
1. client calls send(method, params)
2. Generate sequential request_id
3. Build JSON-RPC request: {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
4. Serialize to JSON + newline
5. Write to stdin
6. Create Future for response
7. Store Future in _pending dict
8. Background reader reads stdout
9. Parse JSON response
10. Match response.id to pending request
11. Set Future result
12. Return response to caller
```

**Concurrency**:
- Multiple concurrent requests supported
- Each request gets unique ID
- Responses matched by ID
- Background reader task handles all responses

**Error Handling**:
- Timeout → Cancel Future, remove from pending
- Malformed JSON → Log warning, skip line
- Process crash → All pending Futures cancelled
- EOF on stdout → Log warning, exit reader task

## Usage Examples

### Start All Auto-Start Servers
```python
registry = ServerRegistry("configs/mcp-servers.json")
registry.load()

process_manager = ProcessManager(registry)
supervisor = Supervisor(registry, process_manager)

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
print(f"PID: {state.process.pid}")
print(f"Restart count: {state.process.restart_count}")
```

### Graceful Shutdown
```python
await supervisor.stop()  # Stops all servers and closes bridges
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

## Testing

### Unit Tests
```python
# Test registry
def test_registry_load():
    registry = ServerRegistry("test-config.json")
    registry.load()
    assert "context7" in registry._servers

# Test process manager
@pytest.mark.asyncio
async def test_process_start():
    mgr = ProcessManager(registry)
    await mgr.start("context7")
    assert mgr.get_process("context7") is not None
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_server_lifecycle():
    supervisor = Supervisor(registry, process_manager)
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
- **Startup time**: 50-200ms per server (Node.js process spawn)
- **Request latency**: 10-50ms (stdio roundtrip)
- **Memory**: 10-50MB per server process
- **Health check overhead**: <10ms (check if process alive)

### Optimization
- Lazy start (auto_start=false for rarely used servers)
- Connection pooling (reuse stdio bridges)
- Batch health checks (check all servers in parallel)

## Troubleshooting

### Server Won't Start
```python
# Check logs
tail -f /tmp/agenthub/audit.log

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

## Related

- [ADR-001: Stdio Transport](../architecture/ADR-001-stdio-transport.md)
- [MCP Specification](https://modelcontextprotocol.io/docs/specification)
- [ProcessManager Source](../../router/servers/process.py)
- [Supervisor Source](../../router/servers/supervisor.py)
