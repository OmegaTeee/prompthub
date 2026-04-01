# ADR-007: Cloud Fallback via OpenRouter Free Tier

## Status
Accepted

## Context
PromptHub's prompt enhancement relies on a local Ollama instance. When Ollama is unavailable (cold start, circuit breaker open, timeout, crash), enhancement silently degrades — the original prompt passes through unchanged. For clients that don't require strict data locality, a cloud fallback can restore enhancement availability.

### Requirements
1. **Privacy-first**: Some clients must never send prompts to the cloud (`local_only`)
2. **Cost-free default**: Fallback should work without paid API keys where possible
3. **Independent failure domain**: Cloud circuit breaker separate from Ollama circuit breaker
4. **Transparent**: Response must indicate which provider served the enhancement

## Decision
Use **OpenRouter's free-tier models** as the cloud fallback provider, gated by the per-client `PrivacyLevel` from ADR-003/Path C.

### Why OpenRouter?
| Criteria | OpenRouter | Together.ai | Groq | Direct DeepSeek API |
|----------|-----------|-------------|------|---------------------|
| Free tier models | Yes (`:free` suffix) | Limited | No free tier | No free tier |
| OpenAI-compatible API | Yes | Yes | Yes | Yes |
| Model variety | 20+ free models | ~3 free | N/A | 1 |
| Rate limits (free) | 20 req/min | Restrictive | N/A | N/A |
| API key required | Yes (free to create) | Yes | Yes | Yes |
| Extra headers | `HTTP-Referer`, `X-Title` | None | None | None |

OpenRouter was chosen because:
- **Free models available**: Models like `deepseek/deepseek-r1-0528:free` provide useful enhancement without cost
- **Reuses existing code**: `OllamaOpenAIClient` works unmodified via the new `extra_headers` field on `OpenAICompatConfig`
- **Model mapping**: `cloud-models.json` maps local model names to free-tier equivalents, so the fallback uses a comparable model
- **Easy to swap**: If OpenRouter becomes unsuitable, changing `OPENROUTER_BASE_URL` to any OpenAI-compatible provider works

### Privacy Gating
The `PrivacyLevel` enum (from Path C) controls fallback eligibility:

| Privacy Level | Cloud Fallback | Use Case |
|---------------|----------------|----------|
| `local_only` | Never | Default for all clients — prompts stay on localhost |
| `free_ok` | OpenRouter free tier | Perplexity, Raycast — search-oriented, non-sensitive |
| `any` | Any cloud provider | Future use — paid APIs, custom endpoints |

### Circuit Breaker
A separate `CircuitBreaker` instance for OpenRouter:
- **Failure threshold**: 2 (vs 3 for Ollama) — fail fast for external service
- **Recovery timeout**: 60s (vs 30s for Ollama) — longer backoff for rate limits
- **Independent**: Ollama failure doesn't affect cloud breaker and vice versa

## Implementation

### Fallback Flow
```
enhance() called
  ↓
Ollama attempt → success? → return (provider="ollama")
  ↓ (failure)
_try_cloud_fallback()
  ├── Gate 1: privacy_level == "local_only"? → return original
  ├── Gate 2: cloud client exists? → return original
  ├── Gate 3: cloud circuit breaker open? → return original
  └── Cloud call → success? → return (provider="openrouter")
                   ↓ (failure)
              return original (graceful degradation)
```

### Configuration
```env
# .env
OPENROUTER_ENABLED=false          # Opt-in (default off)
OPENROUTER_API_KEY=sk-or-...      # Free to create at openrouter.ai
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT=30
OPENROUTER_DEFAULT_MODEL=deepseek/deepseek-r1-0528:free
```

### Model Mapping
`configs/cloud-models.json` contains a `local_models` section mapping local model names to cloud equivalents:
```json
{
  "local_models": [
    {
      "name": "llama3.2:latest",
      "cloud_upgrade": "meta-llama/llama-3.2-3b-instruct:free"
    }
  ],
  "free_models": ["deepseek/deepseek-r1-0528:free", ...]
}
```

### Files Changed
| File | Change |
|------|--------|
| `app/router/enhancement/service.py` | `_try_cloud_fallback()`, cloud client init, `provider` field |
| `app/router/enhancement/ollama_openai.py` | `extra_headers` on `OpenAICompatConfig` |
| `app/router/config/settings.py` | 5 `OPENROUTER_*` settings |
| `app/router/routes/enhancement.py` | `provider` in response |
| `app/configs/cloud-models.json` | Model mapping |
| `app/tests/test_cloud_fallback.py` | 28 tests |

## Consequences

### Positive
- Enhancement works even when Ollama is down (for eligible clients)
- Zero cost with free-tier models
- `OllamaOpenAIClient` is now reusable for any OpenAI-compatible provider
- `provider` field in response enables observability (which backend served the request)

### Negative
- Free-tier rate limits (20 req/min on OpenRouter) may throttle high-volume clients
- Cloud models may produce different quality output than local Ollama models
- Requires API key creation (free but manual step)

### Neutral
- `local_only` clients (the default) are completely unaffected
- Opt-in via `OPENROUTER_ENABLED=true` — no change for existing deployments
- Can be extended to paid tiers by changing `OPENROUTER_DEFAULT_MODEL` to a non-free model

## Related
- [ADR-003: Per-Client Enhancement](ADR-003-per-client-enhancement.md) — Privacy levels extend per-client rules
- [ADR-006: Enhancement Timeout](ADR-006-enhancement-timeout.md) — Cloud fallback activates on the same timeout failures
- Path C (Privacy Boundary) — `PrivacyLevel` enum and downgrade-only header semantics

## Revision History
- 2026-02-27: Initial decision after implementing Path D (cloud fallback)
