# LM Studio API Modes & OpenAI Proxy

PromptHub uses LM Studio (or any OpenAI-compatible local LLM server) in two distinct ways. Understanding the difference avoids configuration confusion.

## Two Concepts

|                  | Enhancement Backend                                 | Client Proxy                                     |
| ---------------- | --------------------------------------------------- | ------------------------------------------------ |
| **What**         | How PromptHub's enhancement service talks to LM Studio | How external apps talk to PromptHub              |
| **Endpoints**    | LM Studio's native `/api/v1/*` or OpenAI-compatible `/v1/*`  | PromptHub's `/v1/chat/completions`, `/v1/models` |
| **Config**       | `LM_STUDIO_API_MODE` in `.env`                      | `API_KEYS_CONFIG` in `.env` → `api-keys.json`    |
| **Auth**         | None (local LM Studio)                              | Bearer token required                            |
| **Can disable?** | Switch between native/openai                        | Always active                                    |

## Enhancement Backend

Controls the API format the enhancement service uses when calling the local LLM host (for example, LM Studio). LM Studio supports both a native API (`/api/v1/*`) and an OpenAI-compatible `/v1/*` surface. The running mode is selected at startup and logged.

## Client Proxy (`/v1/` Endpoints)

External apps connect to PromptHub as if it were an OpenAI API server. This is always active regardless of `LM_STUDIO_API_MODE`.

**Endpoints:**
- `POST /v1/chat/completions` — Chat completion (streaming and non-streaming)
- `GET /v1/models` — List available LM Studio models
- `POST /v1/api-keys/reload` — Hot-reload bearer tokens without restart

**Authentication:** Every request requires a bearer token from `api-keys.json`:

```json
{
  "keys": {
    "sk-prompthub-code-001": {
      "client_name": "vscode",
      "enhance": false,
      "description": "VS Code chat (pass-through)"
    },
    "sk-prompthub-copilot-001": {
      "client_name": "vscode",
      "enhance": false,
      "description": "OAI Copilot extension (pass-through)"
    }
  }
}
```

**Enhancement toggle:** Each token has an `enhance` flag. When `true`, the user's last message is enhanced via the enhancement service (using the model and system prompt from `enhancement-rules.json` for that `client_name`) before being forwarded to LM Studio. When `false`, prompts pass through unchanged.

**Request flow:**
1. Bearer token validated → resolves `client_name`
2. If `enhance: true` → enhancement service rewrites the last user message
3. Request forwarded to LM Studio's `/v1/chat/completions`
4. Response streamed (or returned) to the client

## Configuration

### `.env` variables

```bash
# Enhancement backend
LM_STUDIO_API_MODE=openai
LM_STUDIO_HOST=localhost
LM_STUDIO_PORT=11434
LM_STUDIO_TIMEOUT=120

# Client proxy
API_KEYS_CONFIG=configs/api-keys.json
ENHANCEMENT_RULES_CONFIG=configs/enhancement-rules.json
```

### Enhancement rules (`enhancement-rules.json`)

Each client maps to a task-specific model for prompt enhancement (see [ADR-008](../architecture/ADR-008-task-specific-models.md)). The enhancement model runs *before* the user's requested model:

```json
{
  "default": { "model": "qwen/qwen3-4b-2507" },
  "clients": {
    "claude-desktop": { "model": "qwen/qwen3-4b-2507" },
    "claude-code":    { "model": "qwen/qwen3-4b-2507" },
    "vscode":         { "model": "qwen/qwen3-4b-2507" },
    "raycast":        { "model": "qwen/qwen3-4b-2507" }
  }
}
```

**Model swap note:** Enhancement and chat models are loaded sequentially. Lightweight models like `qwen/qwen3-4b-2507` load in <5s, minimizing swap overhead. For latency-sensitive clients, set `"enhance": false` in `api-keys.json` to skip enhancement entirely.

### Client setup (VS Code example)

In VS Code `settings.json`:
```json
{
  "chat.models": [{
    "id": "qwen/qwen3-4b-2507",
    "provider": "openaiCompatible",
    "url": "http://localhost:9090/v1",
    "apiKey": "sk-prompthub-code-001"
  }]
}
```

## Quick Test

```bash
# 1. List available models
curl -s http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-copilot-001" | python3 -m json.tool
```

```bash
# 2. Chat completion WITHOUT enhancement (pass-through token)
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-copilot-001" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-4b-2507","messages":[{"role":"user","content":"Hello"}]}'
```

```bash
# 3. Chat completion WITH enhancement (enhanced token)
#    The last user message is rewritten by the enhancement service
#    before being forwarded to LM Studio.
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-code-001" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-4b-2507","messages":[{"role":"user","content":"Explain JWT auth"}]}'
```

```bash
# 4. Test enhancement directly via the enhancement endpoint
curl -s -X POST http://localhost:9090/llm/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: vscode" \
  -d '{"prompt":"Explain JWT auth"}' | python3 -m json.tool
```

```bash
# 5. Reload API keys after editing api-keys.json
curl -s -X POST http://localhost:9090/v1/api-keys/reload
```

## Troubleshooting

**"Connection refused"** — Ensure LM Studio (the local model server) is running: `lms server start` or `lms daemon up`, or check the system service status.

**"Missing bearer token" (401)** — Add `Authorization: Bearer <token>` header. Tokens are in `api-keys.json`.

**"Invalid API key" (401)** — Token not found in `api-keys.json`. Reload after edits: `POST /v1/api-keys/reload`.

**"Method Not Allowed" (405)** — You're sending GET to a POST-only endpoint. Use `curl -X POST` or `-d '{...}'`.

**"Model not found"** — Download the model first via the LM Studio CLI: `lms get <model-identifier>`. Check available models on the LM Studio server: `GET /v1/models`.

**Enhancement slow or timing out** — The enhancement service has a 120-second httpx timeout (180s middleware timeout for `/llm/enhance` and `/v1/chat/completions`). If enhancement still times out:
- Set `"enhance": false` for the token in `api-keys.json` to skip enhancement entirely
- Check `tail logs/router-stderr.log` for `LM Studio request timed out` warnings
- See [ADR-006](../architecture/ADR-006-enhancement-timeout.md) for timeout architecture

**Enhancement not working** — Verify: (1) `enhance: true` is set for the token in `api-keys.json`, (2) the token's `client_name` has a matching entry in `enhancement-rules.json`, (3) the enhancement model is downloaded/loaded in LM Studio.

## References

- [LM Studio docs](https://lmstudio.ai/docs/)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [ADR-008: Task-Specific Models](../architecture/ADR-008-task-specific-models.md)
