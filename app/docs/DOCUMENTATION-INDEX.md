# PromptHub Documentation Index

Complete documentation overview for PromptHub.

## 📚 Documentation Structure

```
prompthub/
├── README.md                    # Project overview, quick start, API reference
├── CLAUDE.md                    # Instructions for Claude Code
├── CHANGELOG.md                 # Version history
│
# User guides: ~/Vault/PromptHub/ (Obsidian vault)
│
└── docs/                        # Developer documentation
    ├── README.md                # Developer docs index
    ├── api/                     # API documentation
    │   ├── README.md
    │   └── openapi.yaml         # OpenAPI 3.0 specification
    ├── architecture/            # Architecture & ADRs
    │   ├── README.md
    │   ├── ADR-001-stdio-transport.md
    │   ├── ADR-002-circuit-breaker.md
    │   ├── ADR-003-per-client-enhancement.md
    │   ├── ADR-004-modular-monolith.md
    │   └── ADR-005-async-first.md
    ├── modules/                 # Module documentation
    │   ├── README.md
    │   └── servers.md
    ├── audit/                   # Audit system docs
    │   └── AUDIT-IMPLEMENTATION-COMPLETE.md
    └── features/                # Feature implementation docs
        ├── KEYRING-INTEGRATION-COMPLETE.md
        └── TESTING-IMPLEMENTATION.md
```

## 🎯 Documentation by Audience

### For Users
User guides (installation, integrations, workflows) live in the **Obsidian vault** at `~/Vault/PromptHub/`.

### For Developers
Start here if you want to **contribute** to PromptHub:

1. **[docs/README.md](README.md)** - Developer documentation index
2. **[docs/architecture/](architecture/)** - System architecture and ADRs
3. **[docs/modules/](modules/)** - Module-level documentation
4. **[docs/api/](api/)** - REST API reference (OpenAPI spec)
5. **[CLAUDE.md](../CLAUDE.md)** - Claude Code integration guide

### For Operators
1. **[docs/audit/](audit/)** - Audit logging and security monitoring
2. **Dashboard**: `http://localhost:9090/dashboard` - Real-time monitoring
3. Deployment guides (Docker, LaunchAgent) in Obsidian vault: `~/Vault/PromptHub/Core Setup/`

## 📖 Documentation Categories

### Installation, Setup & Integration Guides
See Obsidian vault: `~/Vault/PromptHub/`

### API Documentation
- [API Overview](api/README.md) - REST endpoints, workflows
- [OpenAPI Spec](api/openapi.yaml) - Machine-readable API spec
- [Main README § API Reference](../README.md#api-reference) - Quick reference

### Architecture
- [Architecture Overview](architecture/README.md) - System design, components
- [ADR-001: Stdio Transport](architecture/ADR-001-stdio-transport.md) - Why stdio
- [ADR-002: Circuit Breaker](architecture/ADR-002-circuit-breaker.md) - Resilience
- [ADR-003: Per-Client Enhancement](architecture/ADR-003-per-client-enhancement.md) - Routing
- [ADR-004: Modular Monolith](architecture/ADR-004-modular-monolith.md) - Architecture choice
- [ADR-005: Async-First](architecture/ADR-005-async-first.md) - Concurrency model

### Module Documentation
- [Module Index](modules/README.md) - All modules overview
- [servers/](modules/servers.md) - MCP server lifecycle
- *(More module docs coming)*

### Audit & Security
- [Audit Implementation](audit/AUDIT-IMPLEMENTATION-COMPLETE.md) - Security score: 9.0/10
- [Keyring Integration](features/KEYRING-INTEGRATION-COMPLETE.md) - Credential management
- [OpenAI-Compatible API Proxy](features/OPENAI-PROXY-COMPLETE.md) - Desktop app integration with router features
- [Security Fixes](../SECURITY-FIXES.md) - Security improvements

## 🔍 Finding Documentation

### By Feature
- **MCP server management** → [modules/servers.md](modules/servers.md)
- **OpenAI-compatible API proxy** → [features/OPENAI-PROXY-COMPLETE.md](features/OPENAI-PROXY-COMPLETE.md)
- **Prompt enhancement** → [ADR-003](architecture/ADR-003-per-client-enhancement.md)
- **Circuit breakers** → [ADR-002](architecture/ADR-002-circuit-breaker.md)
- **Audit logging** → [audit/](audit/)
- **API reference** → [api/](api/)

### By Use Case
- **"How do I install PromptHub?"** → [Getting Started Guide](https://obsidian.md) (Obsidian vault: `~/Vault/PromptHub/01-Getting Started/`)
- **"How do I connect Claude Desktop?"** → [Claude Desktop Integration](https://obsidian.md) (Obsidian vault: `~/Vault/PromptHub/03-Integrations/`)
- **"How do I connect Cursor/Raycast/Obsidian apps?"** → [OpenAI-Compatible API Proxy](features/OPENAI-PROXY-COMPLETE.md)
- **"What's the API endpoint format?"** → [api/README.md](api/README.md)
- **"Why use stdio instead of HTTP?"** → [ADR-001](architecture/ADR-001-stdio-transport.md)
- **"How does auto-restart work?"** → [modules/servers.md § Supervisor](modules/servers.md#supervisor)

### By Role
- **First-time user** → [README.md](../README.md) → [Obsidian vault: Getting Started](https://obsidian.md) (`~/Vault/PromptHub/01-Getting Started/`)
- **Claude Desktop user** → [Obsidian vault: Integrations](https://obsidian.md) (`~/Vault/PromptHub/03-Integrations/`)
- **Developer adding feature** → [architecture/](architecture/) → [modules/](modules/)
- **Operator monitoring** → Dashboard → [audit/](audit/)
- **API consumer** → [api/openapi.yaml](api/openapi.yaml)

## 📝 Documentation Standards

### Format
- **Markdown** for all documentation
- **OpenAPI YAML** for API specs
- **Mermaid** for diagrams (where supported)

### Structure
- **User guides**: Task-oriented, step-by-step
- **API docs**: Reference-style, comprehensive
- **Architecture docs**: Decision-oriented, explain trade-offs
- **Module docs**: Implementation-oriented, show patterns

### Writing Style
- **User guides**: Conversational, examples-first
- **API docs**: Technical, complete, accurate
- **Architecture docs**: Analytical, compare alternatives
- **Code comments**: Explain "why" not "what"

## 🆕 What's New

### Recently Added (2026-02-12)
✅ **OpenAI-Compatible API Proxy**
- Desktop apps (Cursor, Raycast, Obsidian) connect to localhost:9090/v1
- Transparent enhancement pipeline, caching, circuit breaking, audit logging
- Per-client API key configuration and enhancement rules
- Complete implementation with 19 comprehensive tests

### Recently Added (2025-02-02)
✅ **API Documentation**
- Complete OpenAPI 3.0 specification
- API workflows and common patterns
- Client SDK examples

✅ **Architecture Documentation**
- 5 comprehensive ADRs covering key decisions
- System architecture overview
- Design principles and patterns

✅ **Module Documentation**
- Module index with dependency graph
- Detailed servers/ module documentation
- Testing and performance guidelines

✅ **Enhanced README**
- Comprehensive API reference section
- Request/response examples
- Error handling guide

### Coming Soon
- ⏳ **Module documentation** (10 modules pending)
  - 🔴 HIGH: resilience/, enhancement/, audit.py, security_alerts.py
  - 🟡 MEDIUM: middleware/, cache/, config/, dashboard/
  - 🟠 LOW: pipelines/, clients/
  - See [modules/COVERAGE-ANALYSIS.md](modules/COVERAGE-ANALYSIS.md) for prioritization
- Performance optimization guide
- Troubleshooting runbook
- Migration guides (v0.1 → v0.2)

## 🤝 Contributing to Documentation

### Adding Documentation
1. Choose appropriate location:
   - User-facing guides → Obsidian vault (`~/Vault/PromptHub/`)
   - Developer documentation → `docs/`
   - API reference → `docs/api/`
   - Architecture → `docs/architecture/`
   - Module details → `docs/modules/`
   - Code reviews & planning → `docs/reviews/`
   - Feature implementation → `docs/features/`

2. Follow naming conventions:
   - User guides (Obsidian): Task-oriented names (e.g., "04-Workflows/code-development.md")
   - ADRs: `ADR-NNN-decision-name.md`
   - Modules: `module-name.md`
   - Reviews: `YYYY-MM-DD-feature-name-review.md`

3. Update index files:
   - User guides: Update relevant Obsidian vault index
   - Developer docs: Add to relevant `README.md` in docs/
   - Update [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md) if major feature

### Documentation Review Checklist
- [ ] Clear, concise language
- [ ] Code examples that work
- [ ] Links to related docs
- [ ] Screenshots for UI (guides only)
- [ ] Tested all commands/examples
- [ ] No hardcoded values (use placeholders)

## 📞 Getting Help

### Documentation Issues
- **Unclear documentation**: Open issue with "docs" label
- **Missing documentation**: Open issue with "docs" + "enhancement" labels
- **Incorrect documentation**: Open PR with fix

### Quick Help
- **Installation issues**: [Obsidian vault: Getting Started](https://obsidian.md) (`~/Vault/PromptHub/01-Getting Started/`)
- **Integration issues**: [Obsidian vault: Integrations](https://obsidian.md) (`~/Vault/PromptHub/03-Integrations/`) and [Testing guide](https://obsidian.md) (`~/Vault/PromptHub/05-Testing/integration-tests.md`)
- **API questions**: [api/README.md](api/README.md)
- **Architecture questions**: [architecture/README.md](architecture/README.md)

## 📊 Documentation Coverage

### Coverage by Category
- ✅ **Installation**: Complete
- ✅ **Integration**: Complete (3 main clients)
- ✅ **API Reference**: Complete
- ✅ **Architecture**: Complete (5 ADRs)
- 🟡 **Modules**: Partial (1 of 11 documented — see [modules/COVERAGE-ANALYSIS.md](modules/COVERAGE-ANALYSIS.md))
- ✅ **Testing**: Complete
- ✅ **Audit/Security**: Complete
- ✅ **Features**: 3 completed implementations documented

### Next Priorities
1. Document remaining modules (enhancement, resilience, cache)
2. Add troubleshooting runbook
3. Create video walkthroughs for integrations
4. Add performance tuning guide

## 🔗 External Resources

### MCP Protocol
- [MCP Specification](https://modelcontextprotocol.io/docs/specification)
- [MCP Examples](https://github.com/modelcontextprotocol/servers)

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Async in FastAPI](https://fastapi.tiangolo.com/async/)

### Python Patterns
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

### Design References
- [Modular Monolith](https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer)
- [ADR Template](https://github.com/joelparkerhenderson/architecture-decision-record)

---

**Last updated**: 2025-02-02
**Documentation version**: 0.1.0
**PromptHub version**: 0.1.0
