# LM Studio Backend Migration

**Date**: 2026-03-24
**Branch**: `feature/lm-studio-backend`
**Status**: Approved

## Summary

Replace Ollama as PromptHub's local LLM server with LM Studio. Rename all internal "Ollama" references to backend-agnostic "LLM" naming. Delete the native Ollama API code path and the thinking-token shim, leaving one clean OpenAI-compatible client that works with any backend.

LM Studio becomes the model-serving layer. PromptHub keeps its unique value: MCP orchestration, enhancement pipeline, circuit breakers, audit logging, and the HTMX dashboard.

## Motivation

1. **Ollama's `/v1/` endpoint ignores `think: false`** — hybrid-thinking models (qwen3.5, deepseek-r1) emit reasoning tokens that break non-Ollama clients (Raycast, Cursor). We wrote ~150 lines of workaround code routing through the native `/api/chat` endpoint.
2. **LM Studio handles thinking models correctly** at the server level, separating reasoning tokens into proper fields. This eliminates the workaround entirely.
3. **LM Studio adds JIT model loading** with idle TTL auto-eviction — better VRAM management than Ollama's manual `ollama run`/`ollama stop`.
4. **Two code paths is confusing** — the codebase has `OLLAMA_API_MODE=native` and `OLLAMA_API_MODE=openai` switching between two clients. Only the OpenAI-compat path works with LM Studio (and every other server). Removing the native path simplifies the codebase.

## Approach: Clean Rename (Option B)

Abstract the internal layer from "Ollama" to "LLM". Delete native-only code. Keep one OpenAI-compatible client.

### What this preserves

- Enhancement pipeline (per-client model selection, privacy levels, cloud fallback)
- `/v1/` proxy (Raycast, Cursor, OpenAI SDK clients)
- Orchestrator agent (intent classification)
- All MCP infrastructure (servers, bridge, tool registry, gateway)
- Audit, security, dashboard, memory — untouched

### What this removes

- Native Ollama client (`/api/generate`, `/api/tags`) — ~230 lines
- Thinking-token NDJSON-to-SSE shim — ~140 lines
- `OLLAMA_API_MODE` setting and dual-mode switching logic
- Ollama-specific naming throughout

**Net effect**: ~370 fewer lines, one code path instead of two.

## File Changes

### Deleted

| File | Reason |
|---|---|
| `app/router/enhancement/ollama.py` | Native Ollama client (`/api/generate`, `/api/tags`). LM Studio has no native API. |
| `app/router/openai_compat/streaming.py` | Thinking-token shim (Ollama NDJSON to OpenAI SSE translation). LM Studio streams correctly. |

### Renamed

| From | To | Purpose |
|---|---|---|
| `app/router/enhancement/ollama_openai.py` | `app/router/enhancement/llm_client.py` | OpenAI-compatible HTTP client |
| `app/templates/partials/ollama.html` | `app/templates/partials/llm-models.html` | Dashboard models panel |

### Simplified

| File | Changes |
|---|---|
| `app/router/enhancement/__init__.py` | Remove native Ollama exports. Export `LLMClient`, `LLMConfig`, `LLMConnectionError`, `LLMError`. |
| `app/router/enhancement/service.py` | Remove native/openai mode switch. Always use OpenAI-compat client. Remove native error imports. Remove `isinstance(self._ollama, OllamaOpenAIClient)` branching in `_enhance_with_ollama`. This is the most complex single-file change — effectively a rewrite of the enhancement method and its error handling. |
| `app/router/openai_compat/router.py` | Delete `_chat_via_native_api()`, `_ollama_base_from_v1()`, and `stream_ollama_response` import. Remove native `/api/chat` streaming path — streaming goes through standard `/v1/chat/completions`. Rename `ollama_base_url` params, `_ollama_client` var, `resource_type="ollama"` audit strings. Non-streaming uses standard `/v1/chat/completions`. |
| `app/router/openai_compat/models.py` | Update comment referencing `router.enhancement.ollama_openai`. |
| `app/router/orchestrator/agent.py` | Switch from native `OllamaClient` to `LLMClient` (OpenAI-compat). Use `/v1/chat/completions` instead of `/api/generate`. |
| `app/router/main.py` | Remove native `OllamaConfig` construction. Build one `LLMConfig` with OpenAI-compat URL. |
| `app/router/pipelines/documentation.py` | Update docstrings: "Enhance prompt with Ollama" to "Enhance prompt with LLM". |
| `app/router/routes/pipelines.py` | Update docstring: "Enhances it with Ollama" to "Enhances it with LLM". |
| `app/router/memory/router.py` | Update docstrings: "Ollama enhancement" and "Generate context summary via Ollama" to LLM references. |

### Naming Updates

| File | Changes |
|---|---|
| `app/router/config/settings.py` | `ollama_host` to `llm_host`, `ollama_port` to `llm_port`, `ollama_model` to `llm_model`, `ollama_timeout` to `llm_timeout`. Remove `ollama_api_mode`. Keep `OLLAMA_*` as env aliases via `AliasChoices`. Default port: `1234`. Update `model_post_init` host normalization to use new field names. |
| `app/router/routes/enhancement.py` | Route paths: `/ollama/enhance` to `/llm/enhance`, `/ollama/stats` to `/llm/stats`, `/ollama/orchestrate` to `/llm/orchestrate`, `/ollama/reset` to `/llm/reset`. |
| `app/router/routes/health.py` | Health response key: `"ollama"` to `"llm"`. |
| `app/router/dashboard/router.py` | Panel endpoint: `/dashboard/ollama-partial` to `/dashboard/llm-partial`. |
| `app/templates/dashboard.html` | HTMX polling URL and section title updated. |
| `app/templates/partials/stats.html` | "Ollama Status" to "LLM Status". |
| `app/router/middleware/timeout.py` | Timeout path: `"/ollama/enhance"` to `"/llm/enhance"`. |
| `app/.env.example` | Document both old (`OLLAMA_*`) and new (`LLM_*`) variable names. |
| `app/router/enhancement/context_window.py` | Update source comment from `/api/show` to `/v1/models`. |
| `scripts/open-webui/start.sh` | Port default and health check URL. |
| `scripts/prompthub-start.zsh` | Update "Starting Ollama" message, `pgrep -x "ollama"`, `ollama serve` references. Note: this script is Ollama-specific startup — may be retired or made backend-configurable. |
| `scripts/prompthub-kill.zsh` | Update "kill Ollama" message, `killall ollama` references. Same note as above. |
| `docs/api/openapi.yaml` | Update `/ollama/*` endpoint paths to `/llm/*`. |

### Documentation Updates

These files contain Ollama references that must be updated to stay accurate for AI agent context:

| File | Changes |
|---|---|
| `CLAUDE.md` | Update module table (`enhancement/` description), architecture section, settings table, API endpoints list, env var references (~12 occurrences). |
| `.claude/steering/product.md` | Update Ollama references to "local LLM server". |
| `.claude/steering/tech.md` | Update stack references, Ollama-specific patterns. |
| `.claude/steering/structure.md` | Update module descriptions mentioning Ollama. |

User guides (`docs/guides/01-09`) and architecture docs (`docs/architecture/ADR-*`) contain historical Ollama references. These are follow-up tasks — not blocking for the code migration.

### Test Files

All test files with Ollama imports or references that need updating:

| File | Changes |
|---|---|
| `app/tests/test_enhancement.py` | Update imports from `ollama`/`ollama_openai` to `llm_client`. Update class names. |
| `app/tests/test_openai_compat.py` | Update `stream_ollama_response` import, mock paths. |
| `app/tests/test_endpoints.py` | Update `/ollama/*` route paths to `/llm/*`. |
| `app/tests/test_cloud_fallback.py` | Update Ollama error class imports. |
| `app/tests/unit/test_orchestrator.py` | Update `OllamaClient` import to `LLMClient`. |
| `app/tests/integration/test_enhancement_and_caching.py` | Update enhancement client imports and mock paths. |
| `app/tests/integration/test_client_integrations.py` | Update any Ollama references in integration assertions. |
| `app/pyproject.toml` | Update `requires_ollama` test marker to `requires_llm`. |

### Unchanged

All MCP infrastructure, tool registry, memory, cache, audit, security alerts, bridge, client configs, `enhancement-rules.json`, `api-keys.json`, `cloud-models.json`, `mcp-servers.json`.

## Settings & Configuration

### Environment Variables

| Today | After | Default |
|---|---|---|
| `OLLAMA_HOST` | `LLM_HOST` (alias: `OLLAMA_HOST`) | `localhost` |
| `OLLAMA_PORT` | `LLM_PORT` (alias: `OLLAMA_PORT`) | `1234` |
| `OLLAMA_MODEL` | `LLM_MODEL` (alias: `OLLAMA_MODEL`) | `qwen3.5:2b` |
| `OLLAMA_TIMEOUT` | `LLM_TIMEOUT` (alias: `OLLAMA_TIMEOUT`) | `120` |
| `OLLAMA_API_MODE` | Deleted | Only one mode now |

Alias resolution: if both `LLM_HOST` and `OLLAMA_HOST` are set, `LLM_HOST` wins. Implementation uses Pydantic v2 `AliasChoices` — the first alias that matches in the environment wins:

```python
from pydantic import AliasChoices, Field

class Settings(BaseSettings):
    llm_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("LLM_HOST", "OLLAMA_HOST"),
    )
    llm_port: int = Field(
        default=1234,
        validation_alias=AliasChoices("LLM_PORT", "OLLAMA_PORT"),
    )
    # ... same pattern for llm_model, llm_timeout
```

Note: `validation_alias` overrides default env var resolution, so both names must be listed explicitly in `AliasChoices`. The `model_post_init` host normalization block must also reference the new `llm_host` field name.

### Health Check

Today: `GET /api/tags` (Ollama proprietary).
After: `GET /v1/models` (OpenAI standard, works with both LM Studio and Ollama).

## Routes & API

| Today | After |
|---|---|
| `POST /ollama/enhance` | `POST /llm/enhance` |
| `GET /ollama/stats` | `GET /llm/stats` |
| `POST /ollama/orchestrate` | `POST /llm/orchestrate` |
| `POST /ollama/reset` | `POST /llm/reset` |

All other endpoints unchanged. No external consumers of the `/ollama/*` routes (dashboard-internal only).

## Dashboard & UI

| Element | Today | After |
|---|---|---|
| Panel title | "Ollama Models" | "Local Models" |
| Status label | "Ollama Status" | "LLM Status" |
| Empty state | "No models available (Ollama may be down)" | "No models available (LLM server may be down)" |
| Polling endpoint | `/dashboard/ollama-partial` | `/dashboard/llm-partial` |

## Testing Strategy

### 1. Existing Tests

Run full pytest suite after each change. Tests mock HTTP clients, so no live server needed. Update import paths and class names in test files to match renames.

### 2. Manual Smoke Test

After code changes, with LM Studio running and `qwen3.5:2b` loaded:

- `curl localhost:9090/health` — confirm `"llm": "healthy"`
- `curl localhost:9090/v1/models` — confirm model list
- `curl -X POST localhost:9090/llm/enhance` — confirm enhancement
- Raycast Chat — confirm streaming works without shim

### 3. Rollback Path

Change `LLM_PORT` back to `11434`, start Ollama. The code is backend-agnostic — same OpenAI-compat protocol either way.

## Archived Code

The Ollama-specific workaround code being deleted is already preserved:

- **Thinking-token shim**: `~/Code/ollama-openai-thinking-shim/` (streaming.py, non_streaming.py)
- **MCP HTTP bridge**: https://github.com/OmegaTeee/mcp-http-bridge

## Success Criteria

1. All existing pytest tests pass (with updated imports)
2. PromptHub starts with LM Studio on port 1234
3. `/health` reports `"llm": "healthy"`
4. Enhancement pipeline works end-to-end (`/llm/enhance`)
5. Raycast Chat streams correctly without thinking-token artifacts
6. Orchestrator classifies intents via `/v1/chat/completions`
7. Dashboard shows "Local Models" panel with loaded models
8. Setting `LLM_PORT=11434` and starting Ollama still works (backward compat)
