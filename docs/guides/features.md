# Features

Reference for what PromptHub does once it is running. Setup is in [getting-started.md](getting-started.md); problems are in [operations.md](operations.md).

- [Prompt enhancement](#prompt-enhancement)
- [Enhancement tuning](#enhancement-tuning)
- [Orchestrator](#orchestrator)
- [Session memory](#session-memory)
- [OpenAI-compatible API](#openai-compatible-api)
- [Progressive tool disclosure](#progressive-tool-disclosure)
- [Privacy levels and cloud fallback](#privacy-levels-and-cloud-fallback)

## Prompt enhancement

A local LLM rewrites a prompt to be clearer and more specific before it reaches the chat model or an MCP server. The rewriter sees only the latest user prompt, not history or tool results. On any failure the original prompt passes through unchanged.

Enhancement is off for every client by default. All configured clients in `app/configs/enhancement-rules.json` ship with `"enabled": false`.

### Enable it

1. Set `"enabled": true` on the client's rule in `app/configs/enhancement-rules.json`.
2. Make sure the local LLM server is running (`curl http://localhost:9090/health` shows `"llm":"up"`).
3. Opt in per entry point:

| Entry point | How |
| --- | --- |
| `POST /llm/enhance` | Always runs for the named client |
| `/v1/chat/completions` | The bearer key has `"enhance": true` in `api-keys.json` ([OpenAI-compatible API](#openai-compatible-api)) |
| `POST /mcp/{server}/{path}` | Send `X-Enhance: true` (`true`, `1`, `yes`, `on`), or set `AUTO_ENHANCE_MCP=true` to enhance every proxied MCP request |

Restart the router after editing the rules file.

### Direct call

```bash
curl -s -X POST http://localhost:9090/llm/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: claude-code" \
  -H "X-Privacy-Level: local_only" \
  -d '{"prompt": "fix the login bug"}'
```

The response contains `original`, `enhanced`, `model`, `provider` (`lm-studio` or `openrouter`), `privacy_level`, and `cached`. `enhanced == original` means the rewrite was skipped or failed; the `error` field says why (client disabled, LLM down, privacy blocked cloud fallback).

### MCP proxy opt-in

```bash
curl -s -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: claude-desktop" -H "X-Enhance: true" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"prompt":"Summarize this repo"}}'
```

The middleware looks for the prompt in `params.prompt`, `input`, `message`, `text`, or `arguments.prompt`, replaces it, and forwards the request. `X-Client-Name` chooses the rule; a client with `enabled: false` is not enhanced even with `X-Enhance`. Bodies over `max_enhancement_body_size` are skipped.

### Behavior

- Results are cached (L1 memory, L2 SQLite), keyed on prompt, client, and model.
- A circuit breaker guards the LLM server; when it opens, prompts pass through (or use cloud fallback if allowed).
- Input is capped at 4,096 tokens (`TokenBudget`), truncated at a word boundary with a notice.
- Stats and reset: `GET /llm/stats`, `POST /llm/reset`.

## Enhancement tuning

Rules live in `app/configs/enhancement-rules.json`, which is the source of truth for models and schema:

```json
"claude-code": {
  "enabled": true,
  "model": "qwen3-4b-instruct-2507",
  "model_profile": "coder",
  "system_prompt": "...",
  "temperature": 0.2,
  "max_tokens": 600,
  "privacy_level": "local_only"
}
```

`system_prompt` is sent as the instructions; the user prompt is the message; the model output replaces the original prompt. `privacy_level` is `local_only`, `free_ok`, or `any`.

### Model profiles

A top-level `model_profiles` map defines named bundles (`daemon`, `coder`, `instruct`). A client's `model_profile` selects one; without it the client's own `model` (or the default) applies. Check the result per client:

```bash
curl http://localhost:9090/clients/claude-code/model-profile   # {model_profile, resolved_model, source}
```

Use an instruct model for rewriting. The thinking model (`LLM_ORCHESTRATOR_MODEL`) is for [`/llm/orchestrate`](#orchestrator) only; thinking models emit reasoning tokens and need a larger `max_tokens`. Very small models (sub-1B) tend to echo or truncate input.

### System prompt phrasing

| Avoid | Prefer |
| --- | --- |
| Bracketed parentheticals such as "make the target explicit (URL, path, library)" | Plain prose: "name the file, URL, or library when the user implies one" |
| Output-format templates such as "Format as 'Question: <query>'" | Describe the property: "state the question directly" |
| Tool names in the prompt ("use comet_ask") | "Do not name specific tools." The rewriter does not know the tool set |
| `[REPLACE_ME]` style placeholders (the model copies them literally) | Say "Return only the rewritten prompt, with no explanation, preamble, or quotes." |

Keep system prompts to four goals: clarity, specificity, explicit targets, and format conformance. Do not ask the rewriter to answer the question.

### Sampling

| Setting | Typical | Notes |
| --- | --- | --- |
| `temperature` | 0.2 to 0.3 | 0.1 for code-heavy clients; 0.5 for image-generation prompts (comfyui). Avoid 0.0, which can echo input |
| `max_tokens` | 500 to 600 | 300 for short-answer apps (raycast); about 1,000 for thinking models |

Per-client patterns: code clients (claude-code, vscode, opencode) get low temperature and concrete-target wording; conversational clients (claude-desktop, lm-studio) get light-touch clarity; image clients (comfyui) get descriptive expansion. Copy the closest existing rule when adding a client.

### Debugging

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Output starts with blank lines | Thinking model used as rewriter | Use an instruct model |
| Output cut off | `max_tokens` too low | Raise it |
| Output identical to input | Rewriter too small, or prompt already specific | Use a larger model; test with a vaguer prompt |
| Literal `[URL]` or tool names in output | System prompt phrasing | Rephrase per the table above |
| `provider: openrouter` when you expected local | LLM server down, fallback allowed | `/health` should show `llm: up`; set `privacy_level: local_only` to forbid fallback |
| `enhanced == original`, `error: Enhancement disabled` | `enabled: false` for the client | Set `enabled: true`, restart the router |
| Slow responses | Model too large or thermal throttling | See [operations.md](operations.md#local-llm-and-model-recommendations) |

Run a short set of real prompts through the curl above after each rule change; rewrites should become more concrete without changing meaning.

## Orchestrator

A thinking model (`LLM_ORCHESTRATOR_MODEL`, default `qwen3-4b-thinking-2507`) classifies the prompt's intent, suggests tools, and annotates the prompt before enhancement. It is also callable on its own, which is useful for debugging routing:

```bash
curl -s -X POST http://localhost:9090/llm/orchestrate \
  -H "Content-Type: application/json" -H "X-Client-Name: claude-code" \
  -d '{"prompt": "search the web for the latest FastAPI release notes", "session_context": null}'
```

Request body: `prompt`, optional `session_context`, optional `bypass_cache`. The response includes `intent` and `suggested_tools`. A 503 means the orchestrator agent is not initialized (LLM server unreachable at startup).

## Session memory

SQLite-backed (`$DATA_DIR/memory.db`) context that persists across conversations: sessions hold facts and key-value memory blocks, and can optionally sync with the `memory` MCP server.

| Concept | Meaning |
| --- | --- |
| Session | A conversation container owned by a `client_id`; ID is a full UUID |
| Fact | A short statement with tags and a source (`manual` by default) |
| Memory block | Keyed JSON value (`value` any JSON type), optional `expires_at` (ISO 8601) |

```bash
# create (session_id optional, auto-UUID; memory_mcp_sync optional)
curl -s -X POST http://localhost:9090/sessions -H "Content-Type: application/json" \
  -d '{"client_id": "claude-code"}'

SID=<id from response>
curl -s -X POST http://localhost:9090/sessions/$SID/facts -H "Content-Type: application/json" \
  -d '{"fact": "Project uses FastAPI and SQLite", "tags": ["stack"]}'
curl -s -X PUT  http://localhost:9090/sessions/$SID/memory/preferences -H "Content-Type: application/json" \
  -d '{"value": {"style": "concise"}}'
curl -s http://localhost:9090/sessions/$SID/context        # facts + blocks + MCP graph
curl -s -X POST http://localhost:9090/sessions/search -H "Content-Type: application/json" \
  -d '{"query": "FastAPI", "limit": 10}'                    # cross_client defaults to false
curl -s -X POST http://localhost:9090/sessions/$SID/summarize
curl -s -X DELETE http://localhost:9090/sessions/$SID
```

Other routes: `GET /sessions`, `GET /sessions/{id}/facts`, `DELETE /sessions/{id}/facts/{fact_id}`, `GET`/`DELETE /sessions/{id}/memory/{key}`.

Search is scoped to the caller's client ID, taken from the `X-Client-ID` header (not the body), so one client cannot read another's sessions unless `cross_client` is set. Bridge clients can search memory with the `prompthub_memory_search` meta-tool. The dashboard Memory panel shows sessions and facts. Full model reference: [docs/features/MEMORY-SYSTEM-COMPLETE.md](../features/MEMORY-SYSTEM-COMPLETE.md).

## OpenAI-compatible API

`/v1/` exposes the local LLM server to any OpenAI-compatible app, with bearer auth and optional enhancement. Base URL: `http://localhost:9090/v1`.

| Endpoint | Purpose |
| --- | --- |
| `POST /v1/chat/completions` | Chat (streaming supported with `"stream": true`) |
| `GET /v1/models` | Local models in OpenAI format |
| `GET /v1/api/version` | Liveness probe used by Raycast |
| `POST /v1/responses` | Responses-style requests |
| `POST /v1/api-keys/reload` | Reload `api-keys.json` (admin, no auth) |

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-<client>-001" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-4b-instruct-2507", "messages": [{"role": "user", "content": "Hello"}]}'
```

- Token management is in [getting-started.md](getting-started.md#api-tokens). The key's `client_name` selects rules; `enhance: true` enhances the last user message before it is sent to the model.
- `X-Privacy-Level` may be sent to tighten privacy for one request (it can only downgrade).
- 401: unknown or missing bearer key. 404 on model: pick an ID from `GET /v1/models`.
- Python example: `OpenAI(base_url="http://localhost:9090/v1", api_key="sk-prompthub-<client>-001")`. More examples: [docs/api/integration-examples.md](../api/integration-examples.md); design notes: [docs/features/OPENAI-API.md](../features/OPENAI-API.md).

Typical app setup: set the provider type to "OpenAI compatible", base URL as above, API key as above, and the model to one listed by `/v1/models`.

### Structured output and sampling fields

`/v1/chat/completions` forwards `response_format`, `top_p`, `stop`, `frequency_penalty`, `presence_penalty`, and `user` to the LLM server unchanged, on streaming and non-streaming requests. Fields you leave out are not sent, so the server's defaults apply.

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-<client>-001" \
  -H "Content-Type: application/json" \
  -d '{"model": "<model-id>",
       "messages": [{"role": "user", "content": "Name a European capital."}],
       "response_format": {"type": "json_schema", "json_schema": {"name": "city", "strict": true,
         "schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}}}'
```

The LLM server decides which `response_format` types it supports:

| Server | `json_schema` | `json_object` |
| --- | --- | --- |
| LM Studio | Yes | No (fails with 502) |
| llama.cpp-based servers, e.g. Unsloth Studio | Yes | Yes |

`json_schema` works on both, so prefer it. A `response_format` that is not a JSON object (for example `"json"`) is rejected with 422 before it reaches the server.

## Progressive tool disclosure

With many servers, listing every tool wastes context. The bridge supports two modes:

| Mode | `tools/list` returns |
| --- | --- |
| `full` (default when no profile applies) | Tools for every running server |
| `progressive` | Tier-1 servers' tools, servers loaded on demand, and the meta-tools |

Meta-tools exposed by the bridge: `discover_tools` (lightweight catalog of server, tool, one-line description), `load_server_tools` (adds a server's tools and sends `tools/list_changed`), `prompthub_list_available_servers`, `prompthub_start_server`, and `prompthub_memory_search`. The model discovers, loads, then calls. Loaded servers reset when the bridge restarts or the client reconnects.

Separately, the bridge always minifies tool `inputSchema` (strips `description`, `title`, `examples`, `default`) and truncates descriptions to `DESC_MAX_LENGTH`, which cuts context further in both modes.

### Configure

Option 1, per client in `app/configs/enhancement-rules.json` (preferred):

```json
"claude-code": {
  "tool_profile": { "disclosure": "progressive", "tier1_servers": ["desktop-commander", "context7"] }
}
```

The bridge fetches it at startup from `GET /clients/{CLIENT_NAME}/tool-profile` (`source` shows where it came from). Profiles currently exist for `claude-desktop`, `claude-code`, `codex`, and `vscode`.

Option 2, pin on the bridge via env vars in the client's MCP config:

```json
"env": { "CLIENT_NAME": "claude-code", "TOOL_DISCLOSURE": "progressive", "TIER1_SERVERS": "desktop-commander,context7" }
```

Precedence: env vars, then router profile, then `full`. Setting either env var skips the router fetch. `TOOL_DISCLOSURE=progressive` alone gives an empty tier-1 set; `TIER1_SERVERS` alone does not enable progressive mode.

Choose tier-1 servers for tools used in nearly every session (filesystem and shell, library docs, memory, sequential thinking). Leave occasional servers (search, Obsidian, browser) on-demand. A tier-1 server that is not running is skipped.

### Verify

```bash
curl http://localhost:9090/clients/claude-code/tool-profile
```

Then restart the client fully and check the bridge log (the client's MCP log, e.g. Claude Desktop's `mcp-server-prompthub.log`) for the startup line `Tool disclosure: progressive (tier1: ...)`. Ask the model for a task that needs an unloaded server (for example a web search) and confirm it calls `discover_tools`/`load_server_tools` before the tool. Judge by the tool-call trace, not by the answer.

## Privacy levels and cloud fallback

Each client rule has a `privacy_level` controlling whether a prompt may leave localhost:

| Level | Meaning | Default clients |
| --- | --- | --- |
| `local_only` | Never leaves localhost; if the local LLM fails the original prompt is used | claude-desktop, claude-code, codex, vscode, comfyui, lm-studio, opencode |
| `free_ok` | May fall back to an OpenRouter free-tier model when the local LLM fails | raycast |
| `any` | May use any cloud fallback | none by default |

Rules:

- Strictness order is `local_only` (strictest), `free_ok`, `any`. A request can tighten privacy with `X-Privacy-Level` but never loosen it.
- Cloud fallback also requires `OPENROUTER_ENABLED=true` and an OpenRouter API key in Keychain (`openrouter_api_key`, via `app/scripts/manage-keys.py`), and has its own circuit breaker.
- `app/configs/cloud-models.json` maps local model names to free-tier cloud equivalents; `OPENROUTER_DEFAULT_MODEL` is used when there is no mapping.
- The response reports which backend answered (`provider`) and the effective `privacy_level`.
- Design rationale: [ADR-007](../architecture/ADR-007-cloud-fallback.md).
