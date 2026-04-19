# ADR-009: Orchestrator Agent

## Status
Accepted

## Context
ADR-008 introduced a pre-enhancement classification layer to route prompts through task-specific models. This ADR documents the architectural decisions within that layer — the orchestrator agent itself.

> NOTE: This ADR references historical model tokens in other ADRs (e.g.,
> `qwen3:14b`, `gemma3`, `llama3.2`). These are intentionally preserved here
> for audit/history; review `docs/architecture/ADR-008-task-specific-models.md`
> for the active model mappings before making substitutions.

Quick reference (current): enhancement model = `qwen3-4b-instruct-2507`; the
orchestrator (thinking) model = `qwen3-4b-thinking-2507`. When editing this ADR
for clarity, prefer leaving historical tokens intact and adding a short
parenthetical mapping to the current models above.

### Problem Statement
The enhancement pipeline treated every prompt identically: same model, same system prompt (per client), no awareness of intent. This meant:

- Code prompts and casual questions received the same enhancement
- MCP server suggestions required manual configuration per client
- No session context could influence enhancement behavior
- No way to skip enhancement for trivial prompts

The orchestrator sits upstream of enhancement and must operate under strict constraints: it cannot add perceptible latency, and any failure must be invisible to the user.

## Decision

### 1. Dedicated reasoning model

> **Current model:** `qwen3-4b-thinking-2507` (updated from qwen3:14b (now qwen3-4b-thinking-2507) — see [ADR-008](ADR-008-task-specific-models.md))

Use a separate thinking-variant model for intent classification rather than reusing the enhancement model:

```
incoming prompt
    → OrchestratorAgent.process()   (qwen3-4b-thinking-2507, 2.5s hard ceiling)
    → OrchestratorResult            (intent, tools, annotated prompt)
    → EnhancementService.enhance()  (qwen3-4b-instruct-2507)
    → downstream client
```

The thinking model was chosen because:
- Strong structured output (JSON) with low temperature (0.1)
- Native `<think>` block support (stripped before parsing) for chain-of-thought reasoning
- Same parameter class as the enhancement model, so LM Studio keeps both loaded (~5 GB total)
- Thinking variant provides better classification accuracy than the instruct variant

### 2. Strict 2.5-second timeout with fail-safe pass-through

Every failure mode returns the original prompt unchanged via `OrchestratorResult.pass_through()`:

| Failure | Behavior |
|---------|----------|
| LLM server unavailable | Pass-through (health probe with 10s cooldown) |
| Model not loaded | Pass-through (logged at startup) |
| Timeout (>2.5s) | Pass-through via `asyncio.wait_for` |
| Circuit breaker open | Pass-through (3 failures → 30s recovery) |
| Invalid JSON response | Pass-through (regex fallback attempted first) |
| Any exception | Pass-through (caught, logged) |

The 2.5s ceiling ensures the orchestrator never blocks the enhancement pipeline. Users see no error — enhancement proceeds with the unmodified prompt.

### 3. LRU cache (256 entries, in-process)

Cache key: `sha256(f"{client_name}:{prompt}")[:16]`

- `OrderedDict` with `move_to_end()` on cache hits for true LRU behavior
- Evicts oldest entry when full (FIFO eviction within LRU promotion)
- `bypass_cache=True` parameter for forced re-classification
- Same prompt from different clients produces different cache entries (client name is part of the key)

### 4. Circuit breaker (independent instance)

The orchestrator has its own `CircuitBreaker` separate from the enhancement service:

```python
CircuitBreakerConfig(
    failure_threshold=3,      # 3 consecutive failures → OPEN
    recovery_timeout=30.0,    # 30s before trying again (HALF_OPEN)
    half_open_max_calls=1,    # 1 test call in HALF_OPEN
)
```

This prevents a down LLM server from adding 2.5s of timeout latency to every request — after 3 failures, the circuit opens and requests pass through instantly.

### 5. Token budget for session context injection

The orchestrator can prepend session context to the classification prompt, bounded by a token budget:

```python
CHARS_PER_TOKEN = 4          # ~4 chars per token heuristic
CONTEXT_TOKEN_BUDGET = 800   # Max tokens of session context
```

Budget is enforced by simple character truncation (`session_context[:budget_chars]`). No tokenizer is needed — the heuristic is sufficient for a classification prompt where precision doesn't matter.

The assembled prompt structure:

```
[CLIENT:vscode]
[SESSION_CONTEXT]
{truncated context}
[/SESSION_CONTEXT]
[PROMPT]
{user prompt}
[/PROMPT]
```

### 6. Intent categories and server mapping

Seven intent categories map to suggested MCP servers:

| Intent | Suggested Servers |
|--------|-------------------|
| `code` | desktop-commander, context7, sequential-thinking |
| `documentation` | desktop-commander, sequential-thinking, context7 |
| `search` | context7 |
| `memory` | memory |
| `workflow` | sequential-thinking, desktop-commander |
| `reasoning` | sequential-thinking |
| `general` | (none) |

The model's `suggested_tools` are merged with the intent map (deduped, model suggestions first). This ensures baseline tool coverage even when the model's suggestions are incomplete.

### 7. Health probe cooldown

When the LLM server is unavailable, the agent re-probes at most once every 10 seconds (`HEALTH_PROBE_COOLDOWN`). This prevents flooding the health endpoint under high throughput while still recovering promptly when the server comes back.

## Rationale

### Why not classify within the enhancement prompt?
- Adds latency to every enhancement request (even trivial ones)
- Classification and rewriting are different tasks — a thinking model classifies better than an instruct model
- Orchestrator results cache independently, so repeated similar prompts skip classification entirely

### Why in-process cache instead of SQLite?
- Classification results are ephemeral — they're only useful for the current session
- OrderedDict LRU is fast (O(1) lookup and promotion) with no I/O
- 256 entries ≈ negligible memory footprint
- No persistence needed — cold restarts just rebuild the cache organically

### Why 2.5 seconds and not shorter?
- `qwen3-4b-thinking-2507` typically responds in 0.8–1.5s when warm
- Cold model load can take 5–10s, but the circuit breaker handles repeated cold-start failures
- 2.5s is short enough to be imperceptible in the overall enhancement pipeline (which has 120s httpx + 180s middleware timeouts)
- Shorter timeouts (e.g., 1s) would cause frequent pass-throughs even on warm models under load

### Why a module-level singleton?
- The orchestrator holds an `LLMClient` (httpx connection pool) and circuit breaker state — these should be shared across requests
- `get_orchestrator_agent()` provides lazy initialization with optional config override
- Lifespan manages `initialize()` and `close()` for proper startup/shutdown

## Consequences

### Positive
- Enhancement pipeline is now intent-aware without adding perceptible latency
- MCP server suggestions are automatic (no per-client configuration needed)
- Session context flows into classification decisions
- All failures are invisible to users — the system degrades gracefully to unmodified prompts
- Independent circuit breaker prevents cascading failures from LLM server outages

### Negative
- Additional model to keep loaded (`qwen3-4b-thinking-2507`)
- In-process cache is lost on restart (acceptable — rebuilds quickly)
- LLM output is inherently non-deterministic — JSON parsing must handle malformed responses defensively
- Health probe cooldown means recovery from LLM server restarts takes up to 10s

## Implementation

### Module: `router/orchestrator/`
| File | Purpose |
|------|---------|
| `intent.py` | `IntentCategory` enum, `OrchestratorResult` model, `INTENT_SERVER_MAP` |
| `agent.py` | `OrchestratorAgent` class — model call, JSON parsing, LRU cache, circuit breaker |
| `__init__.py` | Public API exports |

### Configuration Constants (agent.py)
| Constant | Value | Purpose |
|----------|-------|---------|
| `MODEL` | `qwen3-4b-thinking-2507` | Classification model (updated from qwen3:14b (now qwen3-4b-thinking-2507)) |
| `TIMEOUT_SECONDS` | `2.5` | Hard ceiling for `asyncio.wait_for` |
| `MAX_TOKENS` | `300` | Keep JSON responses tight |
| `TEMPERATURE` | `0.1` | Low randomness for reliable structured output |
| `CHARS_PER_TOKEN` | `4` | Token estimation heuristic |
| `CONTEXT_TOKEN_BUDGET` | `800` | Max tokens of session context |
| `HEALTH_PROBE_COOLDOWN` | `10.0` | Seconds between health re-probes |

### Endpoint
```
POST /llm/orchestrate       Classify intent and annotate prompt
     Headers: X-Client-Name
     Response: OrchestrateResponse (intent, suggested_tools, context_hints,
               annotated_prompt, reasoning, confidence, skipped, error)
```

### Test Coverage (17 tests)
| Category | Tests |
|----------|-------|
| `_strip_think_blocks` | 3 (remove, multiline, no-op) |
| `pass_through` factory | 1 |
| `process()` happy path | 2 (code intent, cache hit) |
| `process()` failure paths | 3 (timeout, non-JSON, unhealthy) |
| LLM output validation | 4 (invalid tools type, non-numeric confidence, out-of-range confidence, regex invalid JSON) |
| Cache behavior | 3 (hit, bypass, eviction) |
| Circuit breaker | 1 (open state pass-through) |
| Session context | 1 (truncation to budget) |

## Related
- [ADR-008: Task-Specific Models](ADR-008-task-specific-models.md) — Parent decision that introduced the orchestrator
- [ADR-006: Enhancement Timeout](ADR-006-enhancement-timeout.md) — Timeout tuning retained; orchestrator operates within those bounds
- [ADR-002: Circuit Breaker](ADR-002-circuit-breaker.md) — Same pattern, independent instance
- [ADR-005: Async-First](ADR-005-async-first.md) — `asyncio.wait_for` is the timeout mechanism

## Revision History
- 2026-03-02: Initial decision documenting orchestrator agent architecture
