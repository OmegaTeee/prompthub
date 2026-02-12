## User Request
- Initial: "what is left to do in this project"
- Follow-up: "proceed"

## Action Plan
1) ✅ Baseline review: Read `BUILD-TASKS.md` to align with existing checklist and reconcile gaps.
2) ✅ Runtime hardening (audit): Audited async/httpx usage — documented findings in ASYNC-AUDIT.md.
3) Runtime hardening (fixes): Apply critical and major fixes from audit (circuit breaker for Ollama, aiofiles migration, timeout enforcement).
4) Test expansion: Add unit and integration tests (router core, MCP routing, dashboard) with mocks for external services; wire into CI (pytest, mypy, black).
5) Config and security: Validate Pydantic settings, keychain/secrets handling, and structured logging levels.
6) Docs & examples: Sync getting-started/keychain/launchagent docs and update MCP server config examples.
7) Packaging & release: Add production-ready containerization and formalize release/versioning process.

## Task Tracking
- [x] Review BUILD-TASKS.md and reconcile with current todo list — confirmed Modules 1–10 (MVP core) and 11–17 (server mgmt) are mostly present; gaps remain in tests, container hardening, and dashboard coverage.
- [x] Audit async/await + httpx usage and document findings — Created ASYNC-AUDIT.md with 2 critical, 3 major, 4 minor issues; key gaps: no CB on Ollama, blocking file I/O throughout
- [ ] Add HTTP timeouts everywhere external I/O occurs
- [ ] Ensure circuit breaker wraps all outbound calls (MCP, Ollama, dashboard data)
- [ ] Expand unit tests for router components
- [ ] Mock external services in tests (Ollama, MCP servers)
- [ ] Integration tests for MCP routing (success, timeouts, CB open/half-open)
- [ ] Validate caching strategy and add tests for eviction/hit/miss
- [ ] Harden secrets/keychain flows (error handling, tests)
- [ ] Enforce Pydantic config validation and friendly error surfaces
- [ ] Add dashboard health/stats tests
- [ ] CI pipeline: pytest, mypy, black
- [ ] Containerization (multi-stage Dockerfile, non-root, healthcheck)
- [ ] Docs sync: getting-started, keychain, launchagent, comparison table, examples
- [ ] Release/versioning process (semantic version, changelog)
- [ ] Structured logging defaults and levels