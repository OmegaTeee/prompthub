# Project TODOs

## Deferred Refactors

- [ ] **Enhancement service exception handlers** — `service.py` `enhance()` has 3 near-identical exception handlers (lines ~543-555) with different log levels (`warning`/`error`/`exception`). Consider consolidating if log-level distinction proves unnecessary. Unskip integration tests first (`test_enhancement_and_caching.py`).
- [ ] **Lifespan function length** — `main.py` `lifespan()` is 117 lines initializing 9 services. Break into focused init helpers (`_init_audit()`, `_init_storage()`, `_init_servers()`, `_init_enhancement()`). Requires adding startup integration tests first to catch initialization order regressions.
