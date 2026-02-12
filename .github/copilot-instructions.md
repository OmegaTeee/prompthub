# AgentHub - Copilot Instructions

## Project Overview

AgentHub is a centralized MCP (Model Context Protocol) router for macOS that:

- Unifies MCP server access across desktop apps (Claude, VS Code, Raycast, Obsidian)
- Enhances prompts via local Ollama models before forwarding
- Caches responses (L1 exact match, L2 semantic similarity)
- Provides graceful degradation via circuit breakers

**Single endpoint**: `http://localhost:9090`

## Architecture

This is a **modular monolith** built with FastAPI. The main package is `router/` with these modules:

| Module         | Purpose                                      |
| -------------- | -------------------------------------------- |
| `config/`      | Pydantic settings, JSON config loading       |
| `secrets/`     | macOS Keychain integration                   |
| `routing/`     | MCP server registry, JSON-RPC proxy          |
| `resilience/`  | Circuit breaker pattern                      |
| `cache/`       | L1 in-memory LRU, L2 Qdrant (optional)       |
| `enhancement/` | Ollama client, prompt enhancement middleware |
| `dashboard/`   | HTMX-based observability UI                  |
| `pipelines/`   | Workflow orchestration                       |

## Code Style

### Python

- Use Python 3.11+ features
- Type hints required for all function signatures
- Use `async/await` for I/O operations (httpx, file reads)
- Pydantic for data validation and settings
- Follow PEP 8 with 88-char line limit (Black formatter)

### Patterns to Follow

```python
# Settings via Pydantic
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int = 9090
    class Config:
        env_file = ".env"

# Async HTTP client
import httpx

async def fetch(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Circuit breaker pattern
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.state = CircuitState.CLOSED
        self.failures = 0
```

### Patterns to Avoid

- Don't use `requests` library (use `httpx` for async)
- Don't use global state (use dependency injection)
- Don't hardcode configuration (use Settings class)
- Don't use print() for logging (use `logging` module)

## Key Files

| File                             | Purpose                               |
| -------------------------------- | ------------------------------------- |
| `BUILD-SPEC.md`                  | Consolidated build specification      |
| `BUILD-TASKS.md`                 | Step-by-step implementation checklist |
| `router/main.py`                 | FastAPI application entry point       |
| `configs/mcp-servers.json`       | MCP server registry                   |
| `configs/enhancement-rules.json` | Per-client enhancement rules          |

## API Endpoints

```
GET  /health                    → All services status
GET  /health/{server}           → Single server status
POST /mcp/{server}/{path}       → Forward JSON-RPC to MCP server
POST /ollama/enhance            → Enhance prompt via Ollama
GET  /dashboard                 → HTMX dashboard
```

## Testing

- Use `pytest` with `pytest-asyncio` for async tests
- Mock external services (Ollama, MCP servers) in tests
- Test circuit breaker state transitions
- Test cache hit/miss/eviction

```python
# Example test pattern
import pytest
from router.resilience.circuit_breaker import CircuitBreaker, CircuitState

def test_circuit_opens_after_failures():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
```

## Dependencies

Core dependencies (keep minimal):

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `httpx` - Async HTTP client
- `pydantic` / `pydantic-settings` - Validation
- `jinja2` - Dashboard templates

## Environment Variables

```bash
ROUTER_HOST=0.0.0.0
ROUTER_PORT=9090
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
CACHE_MAX_SIZE=1000
CB_FAILURE_THRESHOLD=3
CB_RECOVERY_TIMEOUT=30
LOG_LEVEL=info
```

## User Guides

See `guides/` for integration guides:

- `getting-started.md` - Quick start
- `keychain-setup.md` - macOS Keychain
- `launchagent-setup.md` - Auto-start setup

## Project Documentation

See `docs/` for development and architecture documentation:

- Project architecture and patterns
- Feature specifications and design docs
- Implementation guides and technical references
- API documentation

## Awesome-Copilot Resources

AgentHub integrates with awesome-copilot collections for development guidance. See:

- [docs/AWESOME-COPILOT-RESOURCES.md](../../docs/AWESOME-COPILOT-RESOURCES.md) - Comprehensive reference of all available collections, instructions, agents, and prompts
- [.github/awesome-copilot-recommendations.md](.github/awesome-copilot-recommendations.md) - Quick reference guide for frequently used agents and generators
- [.github/instructions/AWESOME-COPILOT-INSTRUCTIONS.md](instructions/AWESOME-COPILOT-INSTRUCTIONS.md) - Integration guide with key patterns and requirements

### Key Expert Agents

Use these agents in Copilot Chat by prefixing with `@`:

| Agent | Purpose | Use When |
| ----- | ------- | -------- |
| `@python-mcp-expert` | MCP server development in Python | Building new MCP servers or optimization |
| `@context7` | Latest library versions & best practices | Need current API documentation |
| `@task-planner` | Break features into actionable tasks | Planning sprints or features |
| `@implementation-plan` | Create structured implementation roadmaps | Complex multi-phase features |
| `@se-system-architecture-reviewer` | Architecture review | Reviewing design decisions |
| `@se-security-reviewer` | Security code review | Security-sensitive code |

### Key Instructions

Reference these instructions from awesome-copilot when working on specific areas:

| Instruction | Coverage | File Location |
| ----------- | -------- | -------------- |
| `python-mcp-server.instructions.md` | FastMCP patterns, decorators, async patterns | For MCP server development |
| `python.instructions.md` | PEP 8, type hints, docstrings | All Python code |
| `containerization-docker-best-practices.instructions.md` | Multi-stage builds, security, health checks | Dockerfile and docker-compose |
| `security-and-owasp.instructions.md` | OWASP guidelines, security best practices | Security-sensitive code |

### Integration Checklist

- [ ] Review `python-mcp-server.instructions.md` before implementing MCP servers
- [ ] Check `containerization-docker-best-practices.instructions.md` for Docker improvements
- [ ] Apply `python.instructions.md` standards to all code
- [ ] Reference `security-and-owasp.instructions.md` for security-sensitive code
- [ ] Add HEALTHCHECK directive to Dockerfile
- [ ] Integrate hadolint and Trivy scanning into CI/CD
- [ ] Use `@python-mcp-expert` for MCP server guidance
- [ ] Use task-planner for feature decomposition

## Copilot Workflow

**Processing Files:**

- `Copilot-Processing.md` - Root-level file (like `CLAUDE.md`) for tracking Copilot task processing and findings

**Output Organization:**

- **User-facing guides**: Save in `guides/` (integration instructions, setup tutorials, troubleshooting)
- **Development documentation**: Save in `docs/` (architecture, design decisions, technical specifications)
- **Findings & analysis**: Include in `Copilot-Processing.md` or appropriate guide/doc based on content type

## Common Tasks

### Adding a new MCP server

1. Add entry to `configs/mcp-servers.json`
2. Server will be available at `POST /mcp/{server-name}/tools/call`

### Adding a new client enhancement rule

1. Add entry to `configs/enhancement-rules.json` under `clients`
2. Client identified via `X-Client-Name` header

### Adding a new endpoint

1. Add route in `router/main.py` or appropriate module
2. Use dependency injection for Settings, Cache, etc.
3. Add corresponding test in `tests/`
