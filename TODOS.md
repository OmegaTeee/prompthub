# Project TODOs

## Hygiene

- [ ] **Triage ~18 uncommitted files** — New client configs (`clients/vscode.json`, `zed.json`, `jetbrains.json`), MCP configs (`claude-project.json`, `default.json`, `jetbrains.json`, `perplexity-desktop.json`), `docs/features/OPENAI-API.md`, model sketches, and misc modifications. For each: commit, `.gitignore`, or delete. Run `/hygiene` to audit.

## Deferred Refactors

- [ ] **Enhancement service exception handlers** — `service.py` `enhance()` has 3 near-identical exception handlers (lines ~543-555) with different log levels (`warning`/`error`/`exception`). Consider consolidating if log-level distinction proves unnecessary. Unskip integration tests first (`test_enhancement_and_caching.py`).
- [ ] **Lifespan function length** — `main.py` `lifespan()` is 117 lines initializing 9 services. Break into focused init helpers (`_init_audit()`, `_init_storage()`, `_init_servers()`, `_init_enhancement()`). Requires adding startup integration tests first to catch initialization order regressions.

## Code Review Recommendations (April 2026)


Action: Mock the LLM server in tests (preferred), or increase the timeout for this test. Ensure the test does not depend on external services for reliability. Add a stub/mock for the LLM health check if possible.
