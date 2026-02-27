# Architecture Documentation

Technical architecture and design decisions for PromptHub.

## Architecture Decision Records (ADRs)

ADRs document significant architectural decisions, the context behind them, and their consequences.

### Active ADRs

- [ADR-001: Stdio Transport for MCP Servers](ADR-001-stdio-transport.md)
- [ADR-002: Circuit Breaker Pattern](ADR-002-circuit-breaker.md)
- [ADR-003: Per-Client Prompt Enhancement](ADR-003-per-client-enhancement.md) (model selection amended by ADR-006)
- [ADR-004: Modular Monolith Architecture](ADR-004-modular-monolith.md)
- [ADR-005: Async-First Architecture](ADR-005-async-first.md)
- [ADR-006: Enhancement Timeout & Unified Model](ADR-006-enhancement-timeout.md)

## System Architecture

### High-Level Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Clients   │────▶│  PromptHub    │────▶│ MCP Servers │
│ (Claude,    │     │   Router     │     │ (stdio)     │
│  VS Code,   │     │  :9090       │     │             │
│  Raycast)   │     └──────┬───────┘     └─────────────┘
└─────────────┘            │
                           ▼
                    ┌──────────────┐
                    │   Ollama     │
                    │   :11434     │
                    └──────────────┘
```

### Component Layers

```
┌───────────────────────────────────────────────┐
│              FastAPI Routes                          │
│  /health /servers /mcp /v1 /ollama /sessions /dashboard │
└───────────────┬───────────────────────────────┘
                │
┌───────────────▼───────────────────────────────┐
│             Middleware Stack                  │
│  Timeout → AuditContext → ActivityLogging     │
└───────────────┬───────────────────────────────┘
                │
┌───────────────▼───────────────────────────────┐
│           Service Layer                                  │
│  Supervisor │ Enhancement │ CircuitBreakers │ SessionStorage │
└──────┬──────┴─────┬───────┴───────┬───────────┘
       │            │               │
       ▼            ▼               ▼
┌───────────────┐  ┌─────────┐  ┌───────────┐
│ FastMCPBridge │  │ Ollama  │  │ Resilience│
│  (per-server) │  │ Client  │  │  Patterns │
└───────┬───────┘  └─────────┘  └───────────┘
        │
        ▼
┌───────────────┐
│ FastMCP Client│
│ StdioTransport│
└───────────────┘
```

## Design Principles

### 1. Fail Fast, Fail Safe
- Circuit breakers prevent cascading failures
- Graceful degradation when dependencies unavailable
- Clear error messages with retry guidance

### 2. Async Everything
- Python asyncio for concurrent I/O
- No blocking calls in request path
- Background tasks for monitoring

### 3. Observability First
- Structured logging (JSON format)
- Audit trails for security-relevant operations
- Real-time dashboard with HTMX
- Request correlation via X-Request-ID

### 4. Configuration as Code
- JSON config files (mcp-servers.json, enhancement-rules.json)
- Environment variables for deployment-specific settings
- No hardcoded values

### 5. Security by Default
- Credentials via macOS Keychain
- Audit logging with tamper detection
- Real-time security alerts
- Context propagation via contextvars

## Data Flow

### 1. MCP Proxy Request Flow (`/mcp/{server}/{path}`)

```
Client → FastAPI → CircuitBreaker.check()
   ↓
Server running? → Auto-start if configured
   ↓
FastMCPBridge._dispatch() → FastMCP Client methods
   ↓
FastMCP Client → StdioTransport → subprocess stdin/stdout
   ↓
CircuitBreaker.record_success() → Response
```

### 1b. MCP Gateway Request Flow (`/mcp-direct/mcp`)

```
Client → HTTP POST /mcp-direct/mcp → FastMCP Gateway
   ↓
FastMCPProxy → client_factory() → resolve bridge
   ↓
FastMCP Client → StdioTransport → subprocess stdin/stdout
   ↓
Response (tools namespaced: "server_tool")
```

### 2. Prompt Enhancement Flow

```
Client → FastAPI → EnhancementService
   ↓
Cache hit? → Return cached (keyed by client_name + prompt + model)
   ↓
CircuitBreaker.check() → Ollama available?
   ↓
Select system prompt by client (all clients use llama3.2:latest)
   ↓
Ollama OpenAI API (/v1/chat/completions) → Enhanced prompt → Cache → Response
```

**Timeout chain**: httpx client (120s from .env) → middleware (180s for /ollama/enhance) → Ollama keep_alive (5min before model unload)

### 3. Health Check Flow

```
Timer (10s) → Supervisor.check_all_servers()
   ↓
For each running server:
   ↓
Process alive? → No → Should restart?
   ↓
Yes → Supervisor.restart_server() → Increment restart_count
   ↓
restart_count > max_restarts? → Mark as FAILED
```

## State Management

### Server Lifecycle States

```
STOPPED → STARTING → RUNNING
   ↑                     ↓
   └─────── STOPPING ────┘
            ↓
          FAILED
```

### Circuit Breaker States

```
CLOSED (normal) → OPEN (failing)
   ↑                     ↓
   └─── HALF_OPEN ───────┘
       (testing)
```

## Technology Stack

### Core
- **Python 3.11+** - Modern async features, type hints
- **FastAPI** - High-performance web framework
- **Pydantic** - Data validation and settings
- **Uvicorn** - ASGI server

### MCP Integration
- **FastMCP Client** - MCP server lifecycle and communication
- **StdioTransport** - Subprocess management via stdio
- **FastMCPProxy** - Dynamic client factories for gateway
- **JSON-RPC 2.0** - MCP protocol

### Resilience
- **Circuit breakers** - Custom implementation
- **LRU cache** - Custom OrderedDict with TTL and async locks (cache/memory.py)
- **Retry logic** - httpx built-in

### Observability
- **Logging** - Python stdlib logging
- **SQLite** - Activity log persistence
- **HTMX** - Real-time dashboard updates
- **SHA256** - Audit log integrity

### Security
- **Keyring** - macOS Keychain integration
- **contextvars** - Audit context propagation
- **UUID4** - Request correlation IDs

## Performance Characteristics

### Latency
- **Cache hit**: <1ms (in-memory lookup)
- **MCP request**: 10-100ms (stdio overhead + server processing)
- **Ollama enhancement (warm)**: 5-50s (model loaded in VRAM, depends on prompt + max_tokens)
- **Ollama enhancement (cold)**: 30-60s (model must be loaded into VRAM first)
- **Circuit breaker check**: <0.1ms (state check only)

### Throughput
- **MCP proxy**: ~1000 req/s (limited by MCP server, not router)
- **Enhancement**: ~10 req/s (limited by Ollama throughput)
- **Dashboard**: ~100 concurrent users (HTMX polling)

### Memory
- **Base**: ~50MB (Python + FastAPI)
- **Per MCP server**: ~10-50MB (Node.js process)
- **Cache**: Configurable (default: 500 entries × ~1KB = 500KB)

## Deployment Patterns

### Development

```bash
# Local Python + separate Ollama
uvicorn router.main:app --reload --port 9090
ollama serve
```

### Docker Compose

```bash
# All-in-one container
docker compose up -d
```

### Production (macOS)

```bash
# LaunchAgent for auto-start on login
cp com.prompthub.router.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```

## Scaling Considerations

### Current Limitations
- **Single process** - No horizontal scaling
- **In-memory cache** - Not shared across instances
- **Local Ollama** - Single-threaded LLM inference

### Future Scalability
1. **Multiple routers** + Redis cache = Horizontal scaling
2. **Ollama cluster** + load balancer = Parallel enhancement
3. **WebSocket transport** = Reduce stdio overhead
4. **PostgreSQL** = Persistent activity log with partitioning

## Security Model

### Threat Model
- **In-scope**: Local privilege escalation, credential theft, audit tampering
- **Out-of-scope**: Network attacks (localhost-only), DDoS (single-user)

### Security Controls
1. **Keyring integration** - Credentials never in config files
2. **Audit logging** - Tamper-evident with checksums
3. **Circuit breakers** - Prevent resource exhaustion
4. **Context propagation** - Request correlation for investigations

### Compliance
- **SOC 2**: 90% (audit trails, access controls)
- **GDPR**: 85% (data minimization, audit logs)
- **HIPAA**: 80% (encryption in transit, audit trails)

See [docs/audit/](../audit/) for detailed audit documentation.

## Testing Strategy

### Unit Tests
- **Services**: Enhancement, CircuitBreaker, Cache
- **Managers**: Supervisor, Registry, FastMCPBridge
- **Utilities**: Audit, Security alerts, Integrity

### Integration Tests
- **End-to-end flows**: MCP proxy, enhancement, server lifecycle
- **Error scenarios**: Circuit breaker open, server crash, Ollama down
- **Audit**: Context propagation, security alerts

### Load Tests
- **Locust**: Simulate 100 concurrent users
- **Metrics**: Latency p50/p95/p99, throughput, error rate

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MCP Specification](https://modelcontextprotocol.io/docs/specification)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)
