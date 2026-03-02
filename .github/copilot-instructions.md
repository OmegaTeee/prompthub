# PromptHub - Copilot Instructions

**Canonical reference**: See [CLAUDE.md](../CLAUDE.md) for the full project guide (architecture, modules, endpoints, code style, configuration).

## Quick Context

PromptHub is a centralized MCP router for macOS (`localhost:9090`). Built with FastAPI + Python 3.11+.

## Key Conventions

- Async everywhere: `httpx` (not `requests`), `asyncio` for I/O
- Pydantic for all data validation and settings
- 88-char line limit (ruff format)
- `logging` module, never `print()`
- No global state; use dependency injection
- Route factories use getter callables: `create_X_router(get_service=lambda: service)`

## Development

```bash
cd app && source .venv/bin/activate
uvicorn router.main:app --reload --port 9090   # Run
pytest tests/ -v                                 # Test
ruff check router/ && ruff format router/        # Lint
```

## Project Structure

```
app/router/          # FastAPI application (modular monolith)
app/configs/         # Runtime JSON configs
app/tests/           # Pytest suite (unit/ + integration/)
app/docs/            # Developer docs and ADRs
mcps/                # Node.js MCP bridge + client configs
```
