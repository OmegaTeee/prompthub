# ADR-006: Enhancement Timeout & Unified Model

## Status
Superseded (timeout tuning retained; unified model replaced by [ADR-008](ADR-008-task-specific-models.md) task-specific model strategy — all clients now use `qwen3-4b-instruct-2507` on LM Studio. Ollama references below reflect the state at time of writing.)

> Historical note: this ADR is kept for timeout rationale and migration history.
> The unified `llama3.2` model strategy and Ollama-specific examples below are
> not the current system design. Use [ADR-008](ADR-008-task-specific-models.md)
> for the active enhancement model strategy.

## Context
The prompt enhancement service was failing intermittently — working when the LLM server had the model "hot" in VRAM but silently timing out on cold starts. The root cause was a compound failure across three independent timeout layers.

### Problem Statement
Enhancement requests via `/llm/enhance` were returning the original prompt (graceful degradation) instead of the enhanced version. Direct curl to the LLM server at the same endpoint worked fine, making the failure hard to diagnose.

### Root Cause Analysis

**Three independent timeouts interacted:**

```
httpx client timeout (30s)  ←  too short for cold model load
       ↓ (retries × 3)
middleware timeout (60s)    ←  kills request before retries complete
       ↓
Ollama keep_alive (5min)    ←  unloads model from VRAM after inactivity
```

**Timeline of a cold-start failure:**
1. Ollama unloads llama3.2 from VRAM after 5min of inactivity
2. Enhancement request arrives, httpx sends POST to Ollama
3. Ollama starts loading model into VRAM (4.7GB, takes 30-45s)
4. httpx timeout fires at 30s → "attempt 1 timed out"
5. Retry 1 starts (Ollama still loading) → times out at 30s
6. Middleware kills the entire request at 60s
7. Enhancement returns original prompt (graceful degradation)
8. User sees no error — enhancement silently did nothing

**Compounding factor: model swap thrashing**

ADR-003 specified different models per client (claude-desktop → deepseek-r1, vscode → qwen2.5-coder). On a single-GPU setup, each enhancement request required Ollama to:
1. Unload the current model
2. Load the enhancement model
3. Generate the enhanced prompt
4. Unload the enhancement model
5. Load the chat model for the actual response

This doubled the cold-start penalty and made timeouts nearly guaranteed.

## Decision
Two changes:

### 1. Tiered timeout tuning
- **httpx client**: 120s (from .env `OLLAMA_TIMEOUT=120`, covers cold model loads)
- **Middleware**: 180s for `/llm/enhance` and `/v1/chat/completions` (covers retries)
- **Default middleware**: 60s for all other paths (unchanged)

### 2. Unified enhancement model
All clients use `llama3.2:latest` for enhancement. Per-client differentiation is now via system prompts only, not model selection.

```json
{
  "default": { "model": "llama3.2:latest" },
  "clients": {
    "claude-desktop": { "model": "llama3.2:latest", "system_prompt": "..." },
    "vscode": { "model": "llama3.2:latest", "system_prompt": "..." },
    "raycast": { "model": "llama3.2:latest", "system_prompt": "..." }
  }
}
```

## Rationale

### Why 120s for httpx?
Ollama cold-loads measured at 30-45s for llama3.2 (3.2B Q4_K_M, 4.7GB). With generation time on top, worst case is ~60s. 120s provides 2x headroom for larger models or slower hardware.

### Why unified model?
- Eliminates model swap overhead entirely (LLM server keeps one model warm)
- Reduces cold-start probability (more requests = more frequent keep_alive refresh)
- Per-client system prompts still provide differentiation
- Can be re-expanded later if multi-GPU or LLM server model multiplexing is available

### Why not increase LLM server keep_alive?
- LLM server's `keep_alive` can be set per-model, but requires modifying every request or Modelfile
- Doesn't solve the fundamental timeout mismatch
- Keeping models permanently loaded wastes VRAM on a single-GPU setup

## Consequences

### Positive
- Enhancement works reliably on cold starts (tested: 50.6s cold, <1s cached)
- No model swap thrashing on single-GPU setups
- `.env` timeout propagates to enhancement service (was previously hardcoded at 30s)
- Extended timeout paths configurable per-endpoint in middleware

### Negative
- Per-client model selection is no longer possible without code change (was config-driven)
- 120s timeout means slow failures take longer to surface
- All clients get the same model quality (llama3.2 is smaller than qwen2.5-coder:32b)

### Neutral
- Amends ADR-003 (per-client routing still works for system prompts, just not models)
- Cache key still includes client_name (different system prompts produce different enhancements)

## Implementation

### Files Changed
| File | Change |
|------|--------|
| `app/.env` | `LLM_TIMEOUT=120` (was 30) |
| `app/router/main.py` | Pass `LLMConfig` from settings to `EnhancementService` |
| `app/router/middleware/timeout.py` | Add `/llm/enhance: 180s` to `EXTENDED_TIMEOUT_PATHS` |
| `app/configs/enhancement-rules.json` | All models → `llama3.2:latest` |

### Timeout Configuration

```python
# middleware/timeout.py
EXTENDED_TIMEOUT_PATHS = {
    "/pipelines/documentation": 300.0,
    "/v1/chat/completions": 180.0,
    "/llm/enhance": 180.0,
}
```

```python
# main.py — timeout propagation fix
llm_config = LLMConfig(
    base_url=f"http://{settings.llm_host}:{settings.llm_port}",
    timeout=float(settings.llm_timeout),  # was hardcoded 30.0
)
enhancement_service = EnhancementService(
    rules_path=settings.enhancement_rules_config,
    llm_config=llm_config,
)
```

## Related
- [ADR-003: Per-Client Enhancement](ADR-003-per-client-enhancement.md) — Amended (model selection unified, system prompts remain per-client)
- [ADR-005: Async-First](ADR-005-async-first.md) — httpx async client is the timeout boundary
- `docs/features/OPENAI-API.md` — User-facing timeout troubleshooting
- See [Glossary](../glossary.md) for current terminology

## Revision History
- 2026-02-24: Initial decision after diagnosing intermittent enhancement failures
- 2026-02-28: Superseded by ADR-008 — unified model replaced with task-specific model strategy. Timeout tuning from this ADR is retained unchanged.
