# ADR-008: Task-Specific Models & Orchestrator Agent

## Status
Accepted

## Current model split

PromptHub currently uses a small, stable two-model pattern:

- Enhancement model: `qwen3-4b-instruct-2507`
- Orchestrator model: `qwen3-4b-thinking-2507`

This keeps the enhancement path fast while giving the orchestrator a reasoning-capable model for intent classification and tool suggestions.

## Why this is the current default

- The enhancement path is the hottest path and needs low latency.
- The orchestrator runs before enhancement and is separated from the rewrite step.
- The two-model split remains easy to reason about and easier to maintain than the older per-client matrix.
- LM Studio continues to act as the local inference backend for both roles.

## Current mapping

| Role | Model | Purpose |
|---|---|---|
| Enhancement | `qwen3-4b-instruct-2507` | Fast prompt rewriting for all clients |
| Orchestrator | `qwen3-4b-thinking-2507` | Intent classification and tool hints |

## Operational notes

- Per-client model specialization is intentionally not the default.
- Client-specific overrides remain allowed when they are explicitly configured.
- Failures degrade gracefully: the original prompt continues when enhancement or orchestration fails.

## Related

- [ADR-006: Enhancement Timeout & Unified Model](ADR-006-enhancement-timeout.md)
- [ADR-009: Orchestrator Agent](ADR-009-orchestrator-agent.md)
- [docs/architecture/README.md](README.md)

### Implementation

#### New Module: `router/orchestrator/`
| File | Purpose |
|------|---------|
| `intent.py` | `IntentCategory` enum, `OrchestratorResult` model, `INTENT_SERVER_MAP` |
| `agent.py` | `OrchestratorAgent` class -- model call, JSON parsing, caching, circuit breaker |
| `__init__.py` | Public API exports |

#### Files Changed
| File | Change |
|------|--------|
| `configs/enhancement-rules.json` | Per-client models, temperature, max_tokens, new comfyui client |
| `router/main.py` | Initialize `OrchestratorAgent` in lifespan, pass to enhancement router |
| `router/routes/enhancement.py` | New `POST /llm/orchestrate` endpoint |
| `router/openai_compat/router.py` | Guard against placeholder model names |
| `tests/unit/test_orchestrator.py` | 8 unit tests (mocked LM Studio) |

#### New Endpoint
```
POST /llm/orchestrate    Classify intent and annotate prompt (thinking model)
                         Headers: X-Client-Name
                         Returns: intent, suggested_tools, context_hints,
                                  annotated_prompt, reasoning, confidence
```

## Related
- [ADR-009: Orchestrator Agent](ADR-009-orchestrator-agent.md) -- Deep-dive into orchestrator architecture (timeout, cache, circuit breaker, token budget)
- [ADR-006: Enhancement Timeout](ADR-006-enhancement-timeout.md) -- Superseded (timeout tuning retained, unified model replaced)
- [ADR-003: Per-Client Enhancement](ADR-003-per-client-enhancement.md) -- Extended (per-client now includes model selection again)

## Revision History
- 2026-02-28: Initial decision -- task-specific models and orchestrator agent
- 2026-03-28: Simplified to two-model architecture (Qwen3 4B + Qwen3 4B Thinking), removed per-client specialization, replaced LLM with LM Studio
