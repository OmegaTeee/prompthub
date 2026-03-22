# ADR-008: Task-Specific Models & Orchestrator Agent

## Status
Accepted

## Context
ADR-006 mandated a single unified model (`llama3.2:latest`) for all enhancement clients to avoid VRAM swap thrashing on single-GPU setups. While this solved the cold-start timeout problem, it had drawbacks:

- All clients received the same model quality regardless of task complexity
- Code-focused clients (claude-code, vscode) used a general-purpose model instead of a code-specialized one
- No intent classification — every prompt went through the same enhancement path
- Image generation clients (comfyui) need prompt expansion, not prompt rewriting

The introduction of newer, efficient models (gemma3, qwen3) and Ollama's improved model caching made the single-model constraint unnecessarily restrictive.

## Decision

### 1. Task-specific enhancement models
Replace the unified `llama3.2:latest` with models matched to client workloads:

| Client | Model | Rationale |
|--------|-------|-----------|
| default, vscode, raycast, perplexity, cursor | `gemma3:4b` | Fast, lightweight rewriting |
| claude-desktop | `gemma3:27b` | Higher quality for primary reasoning client |
| claude-code | `qwen3-coder:30b` | Code-specialized model |
| comfyui | `gemma3:4b` | Image prompt expansion (new client) |

### 2. Orchestrator agent (new module)
Add a pre-enhancement classification layer using `qwen3:14b`:

```
incoming prompt
    → OrchestratorAgent.process()   (qwen3:14b, 2.5s timeout)
    → OrchestratorResult            (intent + suggested_tools + annotated_prompt)
    → EnhancementService.enhance()  (per-client model)
    → downstream client
```

The orchestrator classifies prompts into intent categories (`code`, `documentation`, `search`, `memory`, `workflow`, `reasoning`, `general`) and suggests relevant MCP servers. It operates with a strict 2.5s timeout and its own circuit breaker — any failure passes the original prompt through unchanged.

### 3. Updated fallback chain
```json
"fallback_chain": ["gemma3:4b", "gemma3:27b", null]
```

## Rationale

### Why abandon the unified model?
- **gemma3:4b** (3B params) loads in <5s vs llama3.2's 30-45s cold start — swap penalty is now minimal
- Ollama's model caching has improved; frequently-used models stay warm longer
- Code-specialized models (qwen3-coder) produce measurably better enhancement for code prompts
- The timeout tuning from ADR-006 (httpx 120s, middleware 180s) provides sufficient headroom for the larger models

### Why a separate orchestrator model?
- Intent classification needs reasoning capability (qwen3:14b) but runs infrequently and with strict token limits (300 max)
- Enhancement models need to be fast for every request — keeping them small (4b) ensures low latency
- Separation of concerns: orchestrator decides *what* to do, enhancer does the rewriting

### Why not embed classification in the enhancement prompt?
- Would increase enhancement latency for every request
- Classification and rewriting are different skills — specialized models do each better
- Orchestrator results are cached independently (256-entry LRU)

## Consequences

### Positive
- Per-client model quality matched to task complexity
- Code clients get code-specialized enhancement
- New client types (comfyui) supported with task-appropriate prompts
- Intent classification enables future routing decisions (tool suggestions, pipeline selection)

### Negative
- Multiple models may compete for VRAM on constrained hardware
- Orchestrator adds ~1-2s latency on cache misses (mitigated by 2.5s timeout + pass-through)
- More models to pull and maintain (`ollama pull gemma3:4b gemma3:27b qwen3:14b qwen3-coder:30b`)

### Mitigations
- Orchestrator and enhancement models are different sizes — Ollama can often keep both warm
- All failures are graceful: orchestrator timeout → pass-through, enhancement timeout → original prompt
- Fallback chain ensures degradation to smaller models if larger ones fail

## Implementation

### New Module: `router/orchestrator/`
| File | Purpose |
|------|---------|
| `intent.py` | `IntentCategory` enum, `OrchestratorResult` model, `INTENT_SERVER_MAP` |
| `agent.py` | `OrchestratorAgent` class — model call, JSON parsing, caching, circuit breaker |
| `__init__.py` | Public API exports |

### Files Changed
| File | Change |
|------|--------|
| `configs/enhancement-rules.json` | Per-client models, temperature, max_tokens, new comfyui client |
| `router/main.py` | Initialize `OrchestratorAgent` in lifespan, pass to enhancement router |
| `router/routes/enhancement.py` | New `POST /ollama/orchestrate` endpoint |
| `router/openai_compat/router.py` | Guard against placeholder model names |
| `tests/unit/test_orchestrator.py` | 8 unit tests (mocked Ollama) |

### New Endpoint
```
POST /ollama/orchestrate    Classify intent and annotate prompt (qwen3:14b)
                            Headers: X-Client-Name
                            Returns: intent, suggested_tools, context_hints,
                                     annotated_prompt, reasoning, confidence
```

## Related
- [ADR-009: Orchestrator Agent](ADR-009-orchestrator-agent.md) — Deep-dive into orchestrator architecture (timeout, cache, circuit breaker, token budget)
- [ADR-006: Enhancement Timeout](ADR-006-enhancement-timeout.md) — Superseded (timeout tuning retained, unified model replaced)
- [ADR-003: Per-Client Enhancement](ADR-003-per-client-enhancement.md) — Extended (per-client now includes model selection again)

## Revision History
- 2026-02-28: Initial decision — task-specific models and orchestrator agent
