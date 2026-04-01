# ADR-008: Task-Specific Models & Orchestrator Agent

## Status
Accepted (updated 2026-03-28)

## Update 2026-03-28 -- Simplified to Two-Model Architecture

Per-client model specialization has been removed. All clients now use a single enhancement model, and the orchestrator uses the thinking variant of the same architecture. LM Studio replaced Ollama as the inference backend.

### Current Assignment

| Role | Model | Params | Context | Format | Notes |
|------|-------|--------|---------|--------|-------|
| Enhancement (all clients) | `qwen/qwen3-4b-2507` | 4B | 262K | MLX | Fast rewriting for every client |
| Orchestrator (thinking model) | `qwen/qwen3-4b-thinking-2507` | 4B | 262K | MLX | Intent classification with reasoning |
| Embedding (standby) | `text-embedding-nomic-embed-text-v1.5` | -- | -- | GGUF | 84 MB, loaded on demand |

**Total memory footprint: ~5 GB** for both active LLMs (down from ~13 GB+ under the previous multi-model setup).

### Why simplify?

1. **Same architecture, simultaneous loading** -- Both models share the Qwen3 4B architecture. LM Studio keeps both loaded without JIT model swapping, eliminating the cold-start thrashing that motivated ADR-006.
2. **Lower memory** -- Two 4B models vs. a mix of 4B/14B/27B/30B models. Frees headroom for other workloads on the Mac.
3. **Simpler to maintain** -- One enhancement model to tune, one thinking model for orchestration. No per-client model matrix to track.
4. **262K context on both models** -- The previous orchestrator (14B, 40K ctx) had a much smaller context window. The thinking variant provides reasoning capability within the same resource envelope.
5. **LM Studio backend** -- Replaced Ollama. LM Studio provides native MLX acceleration on Apple Silicon, a built-in model catalog, and a stable OpenAI-compatible API.

### What was removed

- Per-client model assignments (gemma3:4b, gemma3:27b, qwen3-coder:30b) -- all clients use the same enhancement model
- Multi-model fallback chain -- single model, simpler failure mode
- Ollama-specific references -- LM Studio is the inference backend

---

## Original Decision Context (2026-02-28)

*The sections below are preserved as historical record of the original rationale.*

### Context
ADR-006 mandated a single unified model (`llama3.2:latest`) for all enhancement clients to avoid VRAM swap thrashing on single-GPU setups. While this solved the cold-start timeout problem, it had drawbacks:

- All clients received the same model quality regardless of task complexity
- Code-focused clients (claude-code, vscode) used a general-purpose model instead of a code-specialized one
- No intent classification -- every prompt went through the same enhancement path
- Image generation clients (comfyui) need prompt expansion, not prompt rewriting

The introduction of newer, efficient models (gemma3, qwen3) and improved model caching on local LLM servers made the single-model constraint unnecessarily restrictive.

### Decision

#### 1. Task-specific enhancement models (superseded 2026-03-28)
The original plan assigned different models per client workload:

| Client | Model | Rationale |
|--------|-------|-----------|
| default, vscode, raycast, perplexity, cursor | `gemma3:4b` | Fast, lightweight rewriting |
| claude-desktop | `gemma3:27b` | Higher quality for primary reasoning client |
| claude-code | `qwen3-coder:30b` | Code-specialized model |
| comfyui | `gemma3:4b` | Image prompt expansion (new client) |

*This per-client matrix was replaced by a single enhancement model for all clients (see update above).*

#### 2. Orchestrator agent (module retained, model changed)
A pre-enhancement classification layer originally used `qwen3:14b`. Now uses the thinking model (`qwen/qwen3-4b-thinking-2507`):

```
incoming prompt
    -> OrchestratorAgent.process()   (thinking model, 2.5s timeout)
    -> OrchestratorResult            (intent + suggested_tools + annotated_prompt)
    -> EnhancementService.enhance()  (enhancement model)
    -> downstream client
```

The orchestrator classifies prompts into intent categories (`code`, `documentation`, `search`, `memory`, `workflow`, `reasoning`, `general`) and suggests relevant MCP servers. It operates with a strict 2.5s timeout and its own circuit breaker -- any failure passes the original prompt through unchanged.

#### 3. Updated fallback chain (superseded 2026-03-28)
The original multi-model fallback chain has been removed. With a single small model, enhancement either succeeds or the original prompt passes through unchanged.

### Rationale

#### Why abandon the unified model? (original reasoning)
- **gemma3:4b** (3B params) loads in <5s vs llama3.2's 30-45s cold start -- swap penalty is now minimal
- Local LLM servers have improved model caching; frequently-used models stay warm longer
- Code-specialized models (qwen3-coder) produce measurably better enhancement for code prompts
- The timeout tuning from ADR-006 (httpx 120s, middleware 180s) provides sufficient headroom for the larger models

#### Why a separate orchestrator model?
- Intent classification needs reasoning capability but runs infrequently and with strict token limits (300 max)
- Enhancement models need to be fast for every request -- keeping them small ensures low latency
- Separation of concerns: orchestrator decides *what* to do, enhancer does the rewriting

#### Why not embed classification in the enhancement prompt?
- Would increase enhancement latency for every request
- Classification and rewriting are different skills -- specialized models do each better
- Orchestrator results are cached independently (256-entry LRU)

### Consequences

#### Positive
- Per-client model quality matched to task complexity
- Code clients get code-specialized enhancement
- New client types (comfyui) supported with task-appropriate prompts
- Intent classification enables future routing decisions (tool suggestions, pipeline selection)

#### Negative
- Multiple models may compete for memory on constrained hardware
- Orchestrator adds ~1-2s latency on cache misses (mitigated by 2.5s timeout + pass-through)
- More models to pull and maintain

#### Mitigations
- Orchestrator and enhancement models are different sizes -- LM Studio can often keep both warm
- All failures are graceful: orchestrator timeout -> pass-through, enhancement timeout -> original prompt
- Fallback chain ensures degradation to smaller models if larger ones fail

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
- 2026-03-28: Simplified to two-model architecture (Qwen3 4B + Qwen3 4B Thinking), removed per-client specialization, replaced Ollama with LM Studio
