# Developer Documentation

Technical documentation for PromptHub developers and maintainers.

```bash
cd ~/prompthub
source .venv/bin/activate
uvicorn router.main:app --host 127.0.0.1 --port 9090 --reload
```

## Folders

| Folder                             | Contents                                                                     |
| ---------------------------------- | ---------------------------------------------------------------------------- |
| **[api/](api/)**                   | OpenAPI spec, endpoint reference, enhancement API                            |
| **[architecture/](architecture/)** | ADRs (stdio, circuit breaker, async-first, etc.) and comparison docs         |
| **[audit/](audit/)**               | Audit system summary, Phase 1 & 3 implementation (Score: 9.0/10)             |
| **[features/](features/)**         | Feature docs (OpenAI proxy, memory system)                                   |
| **[guides/](guides/)**             | Developer guides (auto-enhancement)                                          |
| **[modules/](modules/)**           | Module documentation (servers, tool registry)                                |
| **[archive/](archive/)**           | Completed reviews, superseded docs (date-prefixed)                           |

### Key References

- **[OPENAI-API.md](features/OPENAI-API.md)** — Dual API support (native + OpenAI-compatible)
- **[api/openapi.yaml](api/openapi.yaml)** — Full OpenAPI 3.0 spec (50 endpoints)
- **[audit/AUDIT-IMPLEMENTATION-COMPLETE.md](audit/AUDIT-IMPLEMENTATION-COMPLETE.md)** — Audit system executive summary
- **[modules/servers.md](modules/servers.md)** — Server lifecycle and stdio bridge documentation
- **[features/MEMORY-SYSTEM-COMPLETE.md](features/MEMORY-SYSTEM-COMPLETE.md)** — Session memory and context management
- **[modules/README.md#tool-registry](modules/README.md#tool-registry)** — Tool registry cache and bridge schema minification

#### Contributing

See the project [README.md](../README.md) and [CLAUDE.md](../CLAUDE.md).
