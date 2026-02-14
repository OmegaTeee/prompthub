# Tech Stack — PromptHub

## Core Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.109+ |
| HTTP Client | httpx | 0.26+ (async) |
| Data Validation | Pydantic / pydantic-settings | 2.5+ |
| Templating | Jinja2 | 3.1+ |
| Database | SQLite (aiosqlite) | Async for activity log |
| Credential Store | macOS Keychain (keyring) | 24.0+ |
| Logging | structlog | 25.0+ (JSON structured) |
| Metrics | prometheus_client | 0.20+ |
| MCP Bridge | Node.js | 20+ |

## Build System

```bash
# Python environment
cd app && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Node.js MCP servers
cd mcps && npm install

# Run router
cd app && uvicorn router.main:app --reload --port 9090
```

## Development Commands

```bash
# Tests
cd app && pytest tests/ -v

# Type checking
cd app && mypy router/

# Linting & formatting
cd app && ruff check router/
cd app && ruff format router/

# Health check
curl http://localhost:9090/health
```

## Code Style

- **Line length**: 88 characters (Black/ruff format)
- **Type hints**: Required on all public functions
- **Imports**: Sorted by isort (via ruff)
- **Python features**: 3.11+ (union types `X | None`, match statements)
- **Logging**: Use `logging` module, never `print()`
- **Config**: Use `Settings` class, never hardcode values
- **State**: No globals; use dependency injection
- **Async**: `httpx` for HTTP, `asyncio` for I/O — never `requests`

## Key Patterns

### Factory Functions for Routers
```python
def create_dashboard_router(
    get_servers: Callable, get_cache: Callable
) -> APIRouter:
    router = APIRouter(prefix="/dashboard")
    # ... endpoints as closures over dependencies
    return router
```

### Circuit Breaker States
`CLOSED` (normal) → 3 failures → `OPEN` (reject all) → 30s → `HALF_OPEN` (test one) → success → `CLOSED`

### Audit Events
```python
from router.audit import audit_event
audit_event(
    event_type="admin_action",
    action="start",
    resource_type="server",
    resource_name="context7",
    status="success",
)
```

### Pydantic Settings with .env
```python
class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 9090
    model_config = SettingsConfigDict(env_file=".env")
```
