# ADR-004: Modular Monolith Architecture

## Status
Accepted

## Context
AgentHub needs an architecture that balances:
- **Simplicity**: Easy to understand, deploy, and debug
- **Modularity**: Clear separation of concerns
- **Performance**: Low latency, high throughput
- **Maintainability**: Easy to extend and refactor

### Architecture Options

1. **Monolith** - Single codebase, single deployment
2. **Modular Monolith** - Single deployment, modular codebase
3. **Microservices** - Multiple services, distributed deployment
4. **Serverless** - Function-as-a-Service (FaaS)

## Decision
Implement as a **Modular Monolith** - a single FastAPI application with clear module boundaries.

### Module Structure
```
router/
├── config/          # Settings and configuration
├── servers/         # MCP server lifecycle management
├── routing/         # Request routing (deprecated)
├── resilience/      # Circuit breakers
├── cache/           # Response caching
├── enhancement/     # Ollama prompt enhancement
├── pipelines/       # Workflow orchestration
├── clients/         # Config generators
├── dashboard/       # HTMX monitoring UI
├── middleware/      # Request/response processing
├── audit.py         # Audit logging
├── security_alerts.py # Security monitoring
├── keyring_manager.py # Credential management
└── main.py          # FastAPI application
```

### Module Boundaries
Each module:
- Has clear public interface (exports in `__init__.py`)
- Manages its own data structures
- Can be tested in isolation
- Has minimal dependencies on other modules

## Rationale

### Why Modular Monolith?

#### ✅ Advantages Over Plain Monolith
- **Maintainability**: Clear module boundaries prevent "big ball of mud"
- **Testability**: Modules can be unit tested independently
- **Team scaling**: Different devs can own different modules
- **Refactoring**: Easy to extract module to service later if needed

#### ✅ Advantages Over Microservices
- **No distributed systems complexity**: No network calls, service discovery, or distributed tracing
- **Simple deployment**: Single `uvicorn` command, no orchestration
- **Fast development**: No inter-service contracts or API versioning
- **Easy debugging**: Stack traces work, no correlation IDs needed
- **Low latency**: Function calls instead of HTTP requests (~0.01ms vs ~10ms)

#### ✅ Advantages Over Serverless
- **No cold starts**: Always warm, consistent latency
- **Stateful**: Can maintain connections to MCP servers, caches in memory
- **Cost**: No per-invocation charges, predictable costs
- **Development**: Standard Python debugging, no vendor lock-in

### When Monolith Makes Sense
✅ **Current reality**:
- Single-user application (local macOS deployment)
- Low request volume (< 1000 req/s)
- Tight coupling acceptable (modules naturally interact)
- Operations simplicity critical (no DevOps team)

### When to Migrate Away
Consider microservices when:
- ❌ Multi-user SaaS (need horizontal scaling)
- ❌ Multiple teams (need independent deployment)
- ❌ Polyglot requirements (need different languages)
- ❌ Different scaling profiles (MCP vs Enhancement)

**Current status**: None of these apply → Monolith is correct choice

## Consequences

### Positive
- **Simple deployment**: Docker image, `docker compose up`
- **Easy development**: `uvicorn router.main:app --reload`
- **Fast testing**: `pytest tests/` runs full suite in seconds
- **Low operational overhead**: No Kubernetes, service mesh, or distributed tracing
- **Predictable performance**: No network hops or serialization overhead

### Negative
- **Single point of failure**: If router crashes, all clients affected
- **No independent scaling**: Can't scale MCP management separately from enhancement
- **Shared memory**: Bug in one module can crash entire process
- **Deployment coupling**: All modules deploy together

### Neutral
- **Module extraction possible**: Clean boundaries allow future microservices
- **Horizontal scaling limited**: Can run multiple instances with shared Redis
- **Language choice**: Python throughout (no polyglot benefits)

## Implementation Patterns

### Dependency Injection
```python
# Good: Pass dependencies as constructor arguments
class Supervisor:
    def __init__(
        self,
        registry: ServerRegistry,
        process_manager: ProcessManager,
    ):
        self.registry = registry
        self.process_manager = process_manager

# Bad: Import and instantiate directly
class Supervisor:
    def __init__(self):
        self.registry = ServerRegistry()  # Tight coupling!
```

### Module Exports
```python
# router/enhancement/__init__.py
from router.enhancement.service import EnhancementService
from router.enhancement.ollama import OllamaClient

__all__ = ["EnhancementService", "OllamaClient"]

# Other modules import from package root
from router.enhancement import EnhancementService
```

### Shared Utilities
```python
# router/audit.py - Used by all modules
def audit_event(event_type: str, **kwargs):
    """Central audit logging for all modules"""

# router/config/settings.py - Shared configuration
class Settings(BaseSettings):
    """Global settings loaded from .env"""
```

## Module Responsibilities

### Core Modules

#### `servers/`
- MCP server process lifecycle (start/stop/restart)
- Stdio bridge for JSON-RPC communication
- Process health monitoring
- Automatic restart on failure

#### `enhancement/`
- Ollama client for prompt enhancement
- Per-client rule selection
- Response caching
- Circuit breaker for Ollama

#### `resilience/`
- Circuit breaker pattern implementation
- Failure detection and recovery
- State management (CLOSED/OPEN/HALF_OPEN)

#### `dashboard/`
- HTMX real-time monitoring UI
- Server status display
- Cache and circuit breaker stats
- Quick action buttons

### Support Modules

#### `config/`
- Pydantic settings from .env
- JSON config file loading
- MCP server registry
- Enhancement rules

#### `middleware/`
- Audit context propagation (contextvars)
- Activity logging (HTTP requests)
- CORS configuration

#### `audit.py`
- Structured event logging
- Security alert integration
- Checksum-based integrity

#### `keyring_manager.py`
- Secure credential retrieval
- macOS Keychain integration

## Testing Strategy

### Unit Tests
Test each module in isolation:
```python
# tests/test_enhancement.py
def test_enhancement_service():
    service = EnhancementService(
        rules_path="test-rules.json",
        ollama_config=mock_config,
    )
    # Test without external dependencies
```

### Integration Tests
Test module interactions:
```python
# tests/integration/test_mcp_flow.py
async def test_mcp_request_flow():
    # Full flow: Request → Circuit breaker → Server → Bridge → Response
    response = await client.post("/mcp/context7/tools/call")
    assert response.status_code == 200
```

### End-to-End Tests
Test deployed application:
```bash
# Start router
uvicorn router.main:app --port 9090

# Run E2E tests
pytest tests/e2e/ -v
```

## Deployment

### Development
```bash
# Single command
uvicorn router.main:app --reload --port 9090
```

### Production (Docker)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY router/ router/
COPY configs/ configs/
COPY templates/ templates/

CMD ["uvicorn", "router.main:app", "--host", "0.0.0.0", "--port", "9090"]
```

### Production (macOS LaunchAgent)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ...>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agenthub.router</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/uvicorn</string>
        <string>router.main:app</string>
        <string>--port</string>
        <string>9090</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

## Migration Path to Microservices (If Needed)

### Phase 1: Extract Enhancement Service
```
router/ (monolith)
enhancement-service/ (separate)
```
Benefits:
- Independent scaling (Ollama is CPU-bound)
- Different deployment cadence

### Phase 2: Extract MCP Gateway
```
router/ (API gateway)
mcp-gateway/ (stdio bridges)
enhancement-service/ (Ollama)
```
Benefits:
- Gateway handles routing, auth
- Gateway can scale independently
- MCP processes isolated

### Phase 3: Full Microservices
```
api-gateway/
mcp-management-service/
enhancement-service/
audit-service/
dashboard-service/
```

**Current assessment**: Unnecessary complexity for current requirements

## Metrics

### Performance
- **Request latency**: p50 = 15ms, p95 = 50ms, p99 = 200ms
- **Memory usage**: ~100MB base + 50MB per MCP server
- **Startup time**: ~2s (load config + start auto-servers)

### Maintainability
- **Lines of code**: ~3500 (router/), ~800 (tests/)
- **Module count**: 11 top-level modules
- **Dependency depth**: Max 3 levels (main → service → client)

### Development Speed
- **Hot reload**: <1s to reflect code changes
- **Test suite**: ~10s for full run
- **Build time**: ~30s (Docker image)

## Related
- [ADR-001: Stdio Transport](ADR-001-stdio-transport.md) - Why local-only is acceptable
- [ADR-005: Async-First](ADR-005-async-first.md) - Enables high concurrency in monolith

## References
- [Modular Monolith Primer](https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer)
- [Shopify: Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity)
- [Martin Fowler: MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)

## Revision History
- 2025-01-10: Initial architecture decision
- 2025-02-02: Documented as ADR
