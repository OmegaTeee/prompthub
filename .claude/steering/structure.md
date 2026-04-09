# Structure — PromptHub

## Directory Organization

```
prompthub/
├── app/                          # Python project (FastAPI router)
│   ├── router/                   # FastAPI application package
│   │   ├── main.py               # App factory (~505 lines: globals, lifespan, middleware, dashboard helpers, router wiring)
│   │   ├── routes/               # Route handlers extracted from main.py (health, servers, MCP, enhancement, audit, pipelines)
│   │   ├── audit.py              # Structured JSON audit logging
│   │   ├── audit_integrity.py    # SHA256 tamper detection
│   │   ├── security_alerts.py    # Real-time anomaly detection
│   │   ├── keyring_manager.py    # macOS Keychain integration
│   │   ├── cache/                # L1 in-memory LRU + L2 SQLite persistent cache
│   │   ├── clients/              # Client-related helpers and config support code
│   │   ├── config/               # Pydantic Settings, JSON config loading
│   │   ├── dashboard/            # HTMX monitoring UI (factory router)
│   │   ├── enhancement/          # LLM HTTP client (OpenAI-compat), per-client rules, cloud fallback (OpenRouter)
│   │   ├── orchestrator/         # Pre-enhancement intent classifier (qwen3-4b-thinking-2507)
│   │   ├── middleware/            # Audit context, activity logging
│   │   ├── memory/               # Session memory (SQLite-backed facts, blocks, MCP sync)
│   │   ├── openai_compat/        # OpenAI proxy /v1/* (factory router)
│   │   ├── pipelines/            # Documentation generation workflow
│   │   ├── resilience/           # Circuit breaker (CLOSED→OPEN→HALF_OPEN)
│   │   └── servers/              # MCP server lifecycle (bridge, process, registry, supervisor)
│   ├── tests/                    # Pytest suite
│   ├── configs/                  # Runtime configs (mcp-servers.json, enhancement-rules.json, api-keys.json)
│   ├── templates/                # Jinja2 templates (dashboard HTML)
│   ├── scripts/                  # Shell scripts (dev, manual tests)
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
├── docs/                         # Developer/engineering docs, ADRs, and user guides
│   ├── api/                      # OpenAPI spec + API overview
│   ├── architecture/             # ADRs and transport adapter docs
│   ├── modules/                  # Module docs (servers/ + coverage analysis)
│   ├── features/                 # Completed feature docs
│   ├── guides/                   # User-facing setup and integration guides
│   ├── audit/                    # 3-phase audit implementation
│   └── archive/                  # Historical docs
├── clients/                      # Per-client directories (MCP configs, app settings, llm.txt knowledge files)
│   ├── claude-desktop/           # mcp.json, README.md
│   ├── cherry-studio/            # mcp-servers-example.json, cherry-studio-llm.txt, assets/
│   ├── zed/                      # settings.json, zed-llm.txt
│   ├── jetbrains/                # mcp.json, jetbrains-llm.txt
│   ├── lm-studio/                # mcp.json, lm-studio-llm.txt
│   └── ...                       # 15 client directories total
├── mcps/                         # Node.js MCP servers + unified bridge
│   ├── prompthub-bridge.js       # Stdio bridge aggregating all servers
│   ├── configs/                  # Bridge-specific configs (mcp-inspector only)
│   └── package.json              # npm dependencies (8 MCP packages)
├── .claude/                      # Claude Code configuration
│   ├── steering/                 # AI agent steering docs (product, tech, structure)
│   └── plans/                    # Implementation plans
├── .github/                      # GitHub Copilot agents, instructions, prompts
├── CLAUDE.md                     # Claude Code integration instructions
├── README.md                     # Project overview and API reference
└── CHANGELOG.md                  # Version history
```

## File Naming Conventions

| Category | Pattern | Example |
|----------|---------|---------|
| ADRs | `ADR-NNN-decision-name.md` | `ADR-001-stdio-transport.md` |
| Feature docs | `FEATURE-NAME-COMPLETE.md` | `OPENAI-PROXY-COMPLETE.md` |
| Reviews | `YYYY-MM-DD-feature-name-review.md` | `2026-02-10-test-completion-and-reorganization.md` |
| Archive | `YYYY-MM-DD-topic-archived.md` | `2026-02-13-copilot-processing-archived.md` |
| Config | Kebab-case `.json` | `mcp-servers.json`, `api-keys.json` |
| Python modules | Snake_case `.py` | `keyring_manager.py`, `circuit_breaker.py` |
| Test files | `test_module.py` | `test_openai_compat.py` |

## Module Responsibilities

| Module | Owns | Depends On |
|--------|------|------------|
| `config/` | Settings, env loading | — |
| `servers/` | MCP server lifecycle (spawn, bridge, registry, supervisor) | config/ |
| `resilience/` | Circuit breaker state machine | — |
| `cache/` | LRU cache with hit/miss tracking | — |
| `enhancement/` | LLM client, per-client enhancement rules, cloud fallback | cache/, resilience/ |
| `orchestrator/` | Intent classification, prompt annotation, tool suggestion | enhancement/ (LLMClient), resilience/ |
| `openai_compat/` | Bearer auth, SSE streaming, /v1 endpoints | enhancement/, resilience/ |
| `dashboard/` | HTMX templates, real-time partials | servers/, cache/, enhancement/ |
| `middleware/` | Audit context propagation, activity logging | — |
| `pipelines/` | Multi-step documentation workflow | enhancement/, servers/ |
| `clients/` | Repo-managed client configs, setup scripts, and examples | — |
| `cli/` | MCP Config Manager — path-safe config generation, validation, diagnostics | config/ |

## Documentation Split

| Location | Content | Audience | Reading Level |
|----------|---------|----------|---------------|
| `docs/guides/` | Setup guides, integrations, workflows, troubleshooting | General users | Grade 9–10 (see `user-manual` agent) |
| `docs/` (other) | ADRs, API specs, module docs, audit reports, feature completions | Developers | Technical |
| `~/Vault/PromptHub/` | Personal notes, extended workflows | Users | — |
| `CLAUDE.md` | AI agent instructions | Claude Code | Technical |
| `.claude/steering/` | Product, tech, structure guidance | All AI agents | Technical |
| `clients/<name>/README.md` | Per-client setup instructions | General users | Grade 9–10 |
| `clients/<name>/<client>-llm.txt` | Upstream docs distilled for LLM context | AI agents | Technical |

## Client Knowledge Files

When working on a specific client's configuration, check `clients/<client-name>/` for:
- `README.md` — setup instructions, config paths, CLI commands
- `<client>-llm.txt` — upstream documentation distilled for LLM context (if present)

Read the `llm.txt` before generating configs or troubleshooting client-specific issues. These files contain format details, gotchas, and config examples that are not in the codebase itself.

Current `llm.txt` files include `cherry-studio`, `zed`, `jetbrains`, and
`lm-studio`. Check the client directory for the current set before depending on
an exact count.
