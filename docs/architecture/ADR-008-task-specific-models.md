# ADR-008: Task-Specific Models & Orchestrator Agent

## Status
Accepted (updated 2026-06-01)

> NOTE: ADR-008 is the canonical source for current model assignments. The
> rewrite verification pass flagged model tokens across the docs — ADR-008
> should be consulted when resolving or updating historical model names to
> avoid accidental drift.

Canonical mapping (editor quick-reference):
- Enhancement (default for clients without `model_profile`) → `Qwopus3.5-4B-v3-GGUF` (distilled-Opus 4B)
- Orchestrator (thinking) → `qwen3-4b-thinking-2507`
- Fallback (`model_profile: "instruct"`) → `qwen3-4b-instruct-2507`
- Per-client opt-in models → resolved via `model_profile` (see *Update 2026-06-01* below)

When editing other documents, prefer adding parenthetical mappings such as
`llama3.2 (now qwen3-4b-instruct-2507)` instead of wholesale replacement to
preserve historical context.

## Update 2026-06-01 — Distilled Daemon + Instruct Fallback

The PR-#33 opt-in phase has converged. The distilled-Opus 4B model has been used in parallel with vanilla `qwen3-4b-instruct-2507` long enough to validate it for the always-on daemon role, so the canonical mapping now flips:

- **`default.model` and `model_profiles.daemon`** in `enhancement-rules.json` both move from `qwen3-4b-instruct-2507` → `Qwopus3.5-4B-v3-GGUF`. Clients without a `model_profile` (or with `model_profile: "daemon"`) now resolve to the distilled-Opus 4B.
- **New `model_profiles.instruct`** entry points at the vanilla `qwen3-4b-instruct-2507`. This is the named fallback profile — used either via explicit per-client opt-in (`model_profile: "instruct"`) or by the `fallback_chain` when the distilled daemon is unavailable.
- **`MODEL_CONTEXT_TOKENS`** in `context_window.py` gains `Qwopus3.5-4B-v3-GGUF: 262_144` so daemon-routed clients get accurate token-budget math.
- **`settings.py` `llm_model` default** stays at `qwen3-4b-instruct-2507`. It's the code-level safety net (env-var fallback when nothing else is configured); keeping it pointed at the vanilla model mirrors the "Instruct as fallback" intent at the lowest layer.

### Why this flip now

Three things converged: (a) the distilled set has been the script's `daemon` profile since PR #34, so it's been the downloaded model for weeks of dev-loop use; (b) PR #46 added safetensors `instruct` as an explicit fallback in the download tool — so "Instruct as fallback" is concrete, not aspirational; (c) the `model_profile` mechanism shipped in PR #33 has been stable enough that flipping the named profile's target is a one-line risk, not a structural change.

### Forward direction

Two threads tracked separately:

- **vLLM for the daemon serving layer** — distilled 4B's concurrent-request workload is exactly what vLLM is for. The safetensors path that PR #46 added makes this a switch of inference backend, not a re-download. See [`docs/notes/plans/idea-llmpm-vllm-migration.md`](../notes/plans/idea-llmpm-vllm-migration.md).
- **Per-client `model:` field cleanup** — most clients in `enhancement-rules.json` still have an explicit `model: "qwen3-4b-instruct-2507"` line that overrides the new default. That's not wrong (it pins them to vanilla on purpose, opt-out from the new daemon), but it means the daemon flip only affects clients with no explicit `model`. Worth a separate audit later: should those per-client pins migrate to `model_profile: "instruct"` (named opt-out) or be removed entirely (so they pick up the new daemon)?

## Update 2026-05-25 — Per-Client Model Profiles (Opt-In)

The two-model assignment from 2026-03-28 stays in place as the default. This update introduces an **opt-in mechanism** for steering specific clients to alternate models without changing the daemon default.

### What's new

- `app/configs/enhancement-rules.json` gains a top-level `model_profiles` map and a per-client `model_profile` key.
- `EnhancementService._load_rules_async` resolves a client's `model_profile` to the profile's model id *before* constructing the rule, so the rest of the service is unaware of the indirection.
- Read-only endpoint `GET /clients/{name}/model-profile` returns `{model_profile, resolved_model, source}` where `source ∈ {default, client_override, profile_missing}`. The `profile_missing` value is the operability bit — a typo'd profile name surfaces in the dashboard instead of silently falling back.

### Seeded profiles

| Profile | Model | Used for |
|---|---|---|
| `daemon` | `qwen3-4b-instruct-2507` | Identical to the canonical default (made explicit) |
| `coder` | `Qwopus3.5-9B-Coder-GGUF` | Code-tooling clients (currently `vscode`, `claude-code`) |
| `claude_feel` | `Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF` | Heavier planner — defined but unassigned, ready for a future `lobe-chat` opt-in |

### Why opt-in vs. flipping the default

The original PR draft swapped the daemon default to `Qwopus3.5-4B-v3-GGUF` and rewrote this ADR's canonical mapping accordingly. Review feedback flagged that this collapsed a settled architectural decision with an experimental model change. The split: keep the canonical mapping (and this ADR) stable, ship the *mechanism* as a separate concern, and let individual clients opt in. If the distilled-Qwen set proves itself in `vscode` + `claude-code`, flipping the daemon default becomes a one-line follow-up; if not, reverting the experiment is two key deletions in `enhancement-rules.json`.

### What did *not* change

- Daemon enhancement default — still `qwen3-4b-instruct-2507`.
- Orchestrator model — still `qwen3-4b-thinking-2507` (thinking variant retained; the orchestrator does not currently use `model_profile`).
- LM Studio as inference backend.
- Memory footprint envelope.

---

## Update 2026-03-28 -- Simplified to Two-Model Architecture

Per-client model specialization has been removed. All clients now use a single enhancement model, and the orchestrator uses the thinking variant of the same architecture. LM Studio replaced LLM as the inference backend.

### Current Assignment

| Role | Model | Params | Context | Format | Notes |
|------|-------|--------|---------|--------|-------|
| Enhancement (all clients) | `qwen3-4b-instruct-2507` | 4B | 262K | MLX | Fast rewriting for every client |
| Orchestrator (thinking model) | `qwen3-4b-thinking-2507` | 4B | 262K | MLX | Intent classification with reasoning |
| Embedding (standby) | `text-embedding-nomic-embed-text-v1.5` | -- | -- | GGUF | 84 MB, loaded on demand |

**Total memory footprint: ~5 GB** for both active LLMs (down from ~13 GB+ under the previous multi-model setup).

### Why simplify?

1. **Same architecture, simultaneous loading** -- Both models share the Qwen3 4B architecture. LM Studio keeps both loaded without JIT model swapping, eliminating the cold-start thrashing that motivated ADR-006.
2. **Lower memory** -- Two 4B models vs. a mix of 4B/14B/27B/30B models. Frees headroom for other workloads on the Mac.
3. **Simpler to maintain** -- One enhancement model to tune, one thinking model for orchestration. No per-client model matrix to track.
4. **262K context on both models** -- The previous orchestrator (14B, 40K ctx) had a much smaller context window. The thinking variant provides reasoning capability within the same resource envelope.
5. **LM Studio backend** -- Replaced LLM. LM Studio provides native MLX acceleration on Apple Silicon, a built-in model catalog, and a stable OpenAI-compatible API.

### What was removed

- Per-client model assignments (gemma3 (now qwen3-4b-instruct-2507):4b, gemma3 (now qwen3-4b-instruct-2507):27b, qwen3-coder:30b) -- all clients use the same enhancement model
- Multi-model fallback chain -- single model, simpler failure mode
- LLM-specific references -- LM Studio is the inference backend

---

## Original Decision Context (2026-02-28)

*The sections below are preserved as historical record of the original rationale.*

### Context
ADR-006 mandated a single unified model (`llama3.2:latest`) for all enhancement clients to avoid VRAM swap thrashing on single-GPU setups. While this solved the cold-start timeout problem, it had drawbacks:

- All clients received the same model quality regardless of task complexity
- Code-focused clients (claude-code, vscode) used a general-purpose model instead of a code-specialized one
- No intent classification -- every prompt went through the same enhancement path
- Image generation clients (comfyui) need prompt expansion, not prompt rewriting

The introduction of newer, efficient models (gemma3 (now qwen3-4b-instruct-2507), qwen3) and improved model caching on local LLM servers made the single-model constraint unnecessarily restrictive.

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
A pre-enhancement classification layer originally used `qwen3:14b`. Now uses the thinking model (`qwen3-4b-thinking-2507`):

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
- **gemma3 (now qwen3-4b-instruct-2507):4b** (3B params) loads in <5s vs llama3.2 (now qwen3-4b-instruct-2507)'s 30-45s cold start -- swap penalty is now minimal
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
- 2026-03-28: Simplified to two-model architecture (Qwen3 4B + Qwen3 4B Thinking), removed per-client specialization, replaced LLM with LM Studio
