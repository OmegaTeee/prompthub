# Module Documentation

Detailed documentation for PromptHub's core modules.

**Coverage**: 3 of 14 modules documented — See [COVERAGE-ANALYSIS.md](COVERAGE-ANALYSIS.md)

## Module Index

### Core Modules
- [servers/](servers.md) - MCP server lifecycle management
- [enhancement/](enhancement.md) - Prompt enhancement via Ollama (+ OpenRouter cloud fallback)
- [resilience/](resilience.md) - Circuit breaker pattern
- [routes/](#routes-package) - Route handlers extracted from main.py

### Support Modules
- [config/](config.md) - Settings and configuration management
- [cache/](cache.md) - Response caching (L1 memory + L2 SQLite persistent)
- [memory/](../features/MEMORY-SYSTEM-COMPLETE.md) - Session memory and context management (SQLite)
- [tool_registry/](#tool-registry) - MCP tool definition cache (SQLite, automatic archival)
- [middleware/](middleware.md) - Request/response processing
- [dashboard/](dashboard.md) - HTMX monitoring UI
- [pipelines/](pipelines.md) - Workflow orchestration
- [clients/](clients.md) - Config generators (Python module: `router/clients/`)

### Utilities
- [audit.py](audit.md) - Structured audit logging
- [security_alerts.py](security-alerts.md) - Real-time anomaly detection
- [keyring_manager.py](keyring.md) - Credential management

## Module Dependency Graph

```
main.py (~505 lines: globals, lifespan, middleware, dashboard helpers, router wiring)
  │
  ├── routes/                     # Route handlers (factory pattern)
  │   ├── health.py               # /health, /circuit-breakers
  │   ├── servers.py              # /servers/* CRUD + start/stop/restart
  │   ├── mcp_proxy.py            # /mcp/{server}/{path} + normalize helpers
  │   ├── enhancement.py          # /ollama/enhance, /ollama/stats, /ollama/reset
  │   ├── audit.py                # /audit/activity*, /audit/integrity*, /security/alerts*
  │   ├── pipelines.py            # /pipelines/documentation
  │   └── client_configs.py       # /configs/claude-desktop, /vscode, /raycast
  │
  ├── servers/
  │   ├── registry.py             # ServerRegistry
  │   ├── supervisor.py           # Supervisor
  │   ├── fastmcp_bridge.py       # FastMCPBridge
  │   └── mcp_gateway.py          # build_mcp_gateway (Streamable HTTP)
  │
  ├── enhancement/
  │   ├── service.py              # EnhancementService (Ollama + cloud fallback)
  │   ├── ollama.py               # OllamaClient (native API)
  │   └── ollama_openai.py        # OllamaOpenAIClient (OpenAI-compat, reused for OpenRouter)
  │
  ├── resilience/
  │   └── circuit_breaker.py      # CircuitBreaker, CircuitBreakerRegistry
  │
  ├── middleware/
  │   ├── audit_context.py        # AuditContextMiddleware
  │   ├── activity.py             # ActivityLoggingMiddleware
  │   └── persistent_activity.py  # PersistentActivityLog
  │
  ├── memory/
  │   ├── storage.py              # SessionStorage (aiosqlite)
  │   ├── mcp_client.py           # MemoryMCPClient (optional sync)
  │   ├── models.py               # Pydantic schemas
  │   └── router.py               # create_memory_router
  │
  ├── tool_registry/
  │   ├── storage.py              # ToolRegistryStorage (aiosqlite, cache + archive tables)
  │   ├── models.py               # CachedTool, ToolSnapshot, ToolRegistryStats
  │   └── router.py               # create_tool_registry_router (/tools/* endpoints)
  │
  ├── dashboard/
  │   └── router.py               # create_dashboard_router
  │
  └── config/
      └── settings.py             # Settings (Pydantic BaseSettings)
```

## Routes Package

The `routes/` package contains route handlers extracted from main.py. Each module exports a `create_X_router()` factory that returns an `APIRouter`:

```python
# Example: routes/health.py
def create_health_router(
    get_supervisor: Callable[[], Any],    # lambda: supervisor
    get_registry: Callable[[], Any],
    get_enhancement_service: Callable[[], Any],
    get_circuit_breakers: Callable[[], Any],
) -> APIRouter:
    router = APIRouter(tags=["health"])
    # ... endpoints close over getter callables
    return router
```

**Why getter callables?** Module-level globals are `None` at import time and only populated during `lifespan()`. Passing `lambda: supervisor` defers evaluation to call-time, when globals are initialized. This is the same pattern used by `openai_compat/`, `dashboard/`, and `memory/` routers.

## Module Boundaries

### Clear Interfaces
Each module exports a minimal public API:

```python
# router/enhancement/__init__.py
from router.enhancement.service import EnhancementService
from router.enhancement.ollama import OllamaClient

__all__ = ["EnhancementService", "OllamaClient"]
```

### Dependency Direction
Dependencies flow one direction (no cycles):

```
main.py → servers → config
       → enhancement → resilience → config
       → memory → middleware (audit context)
       → tool_registry (standalone, used by routes/mcp_proxy)
       → middleware → audit
```

### Data Ownership
Each module owns its data structures:
- **servers/**: `ServerConfig`, `ProcessInfo`, `ServerState`
- **enhancement/**: `EnhancementRule`, `EnhancementResult`
- **resilience/**: `CircuitBreakerConfig`, `CircuitBreakerStats`
- **memory/**: `SessionCreate`, `SessionResponse`, `FactCreate`, `MemoryBlockUpsert`
- **tool_registry/**: `CachedTool`, `ToolSnapshot`, `ToolSnapshotSummary`, `ToolRegistryStats`

## Testing Strategy

### Unit Tests
Test modules in isolation with mocks:

```python
# tests/test_enhancement.py
def test_enhancement_service():
    mock_ollama = Mock()
    mock_cache = Mock()

    service = EnhancementService(
        ollama=mock_ollama,
        cache=mock_cache,
    )

    # Test service logic without dependencies
```

### Integration Tests
Test module interactions:

```python
# tests/integration/test_server_flow.py
async def test_server_lifecycle():
    registry = ServerRegistry("configs/mcp-servers.json")
    await registry.load_async()
    supervisor = Supervisor(registry)

    # Test full lifecycle
    await supervisor.start_server("context7")
    assert registry.get_state("context7").status == "running"
```

## Tool Registry

The `tool_registry/` module caches raw MCP tool definitions in SQLite before they are minified by the bridge. This provides:

- **Cache-through proxy**: `tools/list` responses served from SQLite on subsequent requests (24h TTL)
- **Automatic archival**: Old snapshots moved to `tool_cache_archive` on upsert or invalidation
- **Long-term access**: Archived snapshots retained for 90 days (configurable)
- **Serve tracking**: Each cache hit increments `serve_count` and updates `last_served`

### Schema

```sql
tool_cache          -- One row per server (current snapshot)
tool_cache_archive  -- Historical snapshots (auto-populated on replace/invalidate)
```

### Integration

The proxy in `routes/mcp_proxy.py` checks the registry before proxying `tools/list`:
1. Cache hit + fresh → return cached tools (metadata: `"cache": "hit"`)
2. Cache miss/expired → proxy to live server → cache response → return (metadata: `"cache": "miss"`)

Server restarts or manual `POST /tools/{server}/refresh` invalidate the cache.

### Bridge Schema Minification

The Node.js bridge (`mcps/prompthub-bridge.js`) strips verbose fields from tool `inputSchema` before sending to LLM clients:

- **Strips**: `description`, `title`, `examples`, `default`, `$comment`, `$defs`
- **Keeps**: `type`, `properties`, `required`, `enum`, `items`, `format`, `pattern`, constraints
- **Result**: ~67% reduction in tool definition size (~14K tokens saved across 41 tools)
- **Config**: `MINIFY_SCHEMAS=true` (default), `DESC_MAX_LENGTH=200`

## Common Patterns

### Async-First
All public APIs are async:

```python
class EnhancementService:
    async def enhance(self, prompt: str) -> EnhancementResult:
        # All I/O is async
        cached = await self.cache.get(prompt)
        if cached:
            return cached

        result = await self.ollama.generate(prompt)
        await self.cache.set(prompt, result)
        return result
```

### Pydantic Models
All data structures use Pydantic:

```python
from pydantic import BaseModel

class ServerConfig(BaseModel):
    name: str
    package: str
    command: str
    args: list[str]
    auto_start: bool = False

    class Config:
        frozen = True  # Immutable
```

### Logging
Structured logging throughout:

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Server {name} started", extra={
    "server_name": name,
    "pid": process.pid,
})
```

### Error Handling
Custom exceptions with context:

```python
class FastMCPBridgeError(Exception):
    """Error in FastMCP bridge communication."""
    pass

try:
    response = await bridge.send(method, params)
except FastMCPBridgeError as e:
    logger.error(f"Bridge error: {e}")
    raise HTTPException(503, f"Bridge error: {e}") from e
```

## Module Evolution

### Deprecation Process
1. Add deprecation warning to docstring
2. Log warning when used
3. Update documentation
4. Remove after 2 versions

Example:
```python
def old_function():
    """
    DEPRECATED: Use new_function() instead.
    Will be removed in v0.3.0.
    """
    logger.warning("old_function is deprecated, use new_function")
    return new_function()
```

### Extraction to Service
When a module grows large (>1000 LOC), consider extraction:

1. Extract core logic to separate package
2. Add REST API wrapper
3. Update main.py to call HTTP API
4. Deploy as separate service (optional)

Current candidates:
- `enhancement/` (~800 LOC) - Could become separate service for horizontal scaling

## Documentation Standards

### Docstring Format
```python
def function(param1: str, param2: int) -> bool:
    """
    Short one-line description.

    Longer description if needed. Explain behavior,
    edge cases, and usage patterns.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        IOError: When file not found

    Example:
        >>> function("test", 42)
        True
    """
    pass
```

### Module Docstring
```python
"""
Module short description.

Longer description explaining:
- Module purpose and responsibilities
- Key classes and functions
- Usage patterns
- Integration points

Example:
    from router.servers import Supervisor

    supervisor = Supervisor(registry, process_manager)
    await supervisor.start()
```

## Performance Considerations

### Module Load Time
- Keep imports minimal
- Defer heavy imports to function scope
- Use `TYPE_CHECKING` for type hints

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from router.servers import ServerRegistry

def function(registry: "ServerRegistry"):
    # Type hint without import overhead
    pass
```

### Memory Usage
- Use `__slots__` for frequently instantiated classes
- Clear caches with TTL or size limits
- Release resources in `__del__` or context managers

## Security Considerations

### Input Validation
All external inputs validated with Pydantic:

```python
class EnhanceRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    bypass_cache: bool = False
```

### Output Sanitization
Never expose internal details in errors:

```python
# Bad
raise HTTPException(500, str(exception))

# Good
logger.error(f"Internal error: {exception}")
raise HTTPException(500, "Internal server error")
```

### Audit Logging
Security-relevant operations logged:

```python
from router.audit import audit_admin_action

audit_admin_action(
    action="restart",
    server_name=name,
    status="success",
)
```

## Related Documentation

- [Architecture Overview](../architecture/README.md)
- [ADR Index](../architecture/README.md#architecture-decision-records-adrs)
- [API Documentation](../api/README.md)
- User Guides: Obsidian vault at `~/Vault/PromptHub/`
