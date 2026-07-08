---
slug: middleware-architecture
section: syntheses
status: archived-to-wiki
related: docs/architecture/*
---
# Middleware Architecture Overview

This page summarizes the key architectural decisions from the
**Enhancement‑Middleware Review** (Feb 03 2026). Those decisions inform how
Middleware is added to the PromptHub FastAPI router.

## Core Principles
1. **Asynchronous Implementation** – All middleware functions are `async`
   to avoid blocking the event loop.
2. **Graceful Degradation** – Middleware can return a short‑circuit
   response or re‑raise with proper status code.
3. **HTTP‑Layer Exception Handling** – For middleware HTTP responses, rely on
   FastAPI's `HTTPException` rather than custom exception classes.
4. **Instrumented Logging** – Every entry/exit path is logged with the
   running request id for traceability.
5. **Reversible Configuration** – Middleware can be enabled/disabled via
   environment variables (`ENABLE_MIDDLEWARE=True`).

## Typical Implementation
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.middleware("http")
async def enhancer_middleware(request: Request, call_next):
    # Pre‑processing
    try:
        # Validate request payload
        if "x-special-header" not in request.headers:
            raise HTTPException(status_code=400, detail="Missing feature header")

        # Proceed to the main path
        response = await call_next(request)

    except Exception as exc:
        # Log & transform errors
        logger.warning("Middleware error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(exc)})

    # Post‑processing
    response.headers["X-Processed-By"] = "enhancer"
    return response
```

## Safety Nets
- **Circuit Breaker**: If the middleware performs an outbound HTTP call
  (e.g., external feature‑flag service), wrap it with a circuit breaker so
  that repeated failures do not cascade into service outage.
- **Thunk/Stub**: During unit tests provide a *stub* that merely passes the
  request through; this avoids dependency on external services.
- **Health Check Endpoint**: Expose `/health/middleware` to confirm middleware
  is still operational.

## Migration Checklist
- Replace all legacy ``router/decorators.py`` calls with FastAPI
  ``@app.middleware("http")`` style.
- Validate all paths that performed blocking I/O; add async wrappers.
- Add tests that simulate both success and error scenarios.
- Document environment overrides in `docs/configuration/middleware.md`.

## Related Topics
- `docs/architecture/ADR-007-async-middleware.md` – Historical ADR
  explaining async enforcement.
- `docs/architecture/ADR-008-circuit‑breaker.md` – Design decisions
  around outbound calls.
- `docs/architecture/ADR-009-best‑logging.md` – Logging pattern used across
  the router stack.
