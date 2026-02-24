# Ollama API Modes & OpenAI Proxy

PromptHub uses Ollama in two distinct ways. Understanding the difference avoids configuration confusion.

## Two Concepts

|                  | Enhancement Backend                                 | Client Proxy                                     |
| ---------------- | --------------------------------------------------- | ------------------------------------------------ |
| **What**         | How PromptHub's enhancement service talks to Ollama | How external apps talk to PromptHub              |
| **Endpoints**    | Ollama's `/api/generate` or `/v1/chat/completions`  | PromptHub's `/v1/chat/completions`, `/v1/models` |
| **Config**       | `OLLAMA_API_MODE` in `.env`                         | `API_KEYS_CONFIG` in `.env` → `api-keys.json`    |
| **Auth**         | None (local Ollama)                                 | Bearer token required                            |
| **Can disable?** | Switch between native/openai                        | Always active                                    |

## Enhancement Backend (`OLLAMA_API_MODE`)

Controls the API format the enhancement service uses when calling Ollama to improve prompts before forwarding them.

```bash
# .env
OLLAMA_API_MODE=native   # Default: uses /api/generate
OLLAMA_API_MODE=openai   # Alternative: uses /v1/chat/completions
```

Both modes produce identical results — the difference is the wire format. Use `native` unless you have a specific reason to use the OpenAI format (e.g., an Ollama-compatible proxy that only speaks OpenAI).

The mode is selected at startup and logged:
```
INFO: Using native Ollama API
# or
INFO: Using OpenAI-compatible Ollama API
```

## Client Proxy (`/v1/` Endpoints)

External apps connect to PromptHub as if it were an OpenAI API server. This is always active regardless of `OLLAMA_API_MODE`.

**Endpoints:**
- `POST /v1/chat/completions` — Chat completion (streaming and non-streaming)
- `GET /v1/models` — List available Ollama models
- `POST /v1/api-keys/reload` — Hot-reload bearer tokens without restart

**Authentication:** Every request requires a bearer token from `api-keys.json`:

```json
{
  "keys": {
    "sk-prompthub-code-dev001": {
      "client_name": "vscode",
      "enhance": true,
      "description": "VS Code chat"
    }
  }
}
```

**Enhancement toggle:** Each token has an `enhance` flag. When `true`, the user's last message is enhanced via the enhancement service (using the model and system prompt from `enhancement-rules.json` for that `client_name`) before being forwarded to Ollama. When `false`, prompts pass through unchanged.

**Request flow:**
1. Bearer token validated → resolves `client_name`
2. If `enhance: true` → enhancement service rewrites the last user message
3. Request forwarded to Ollama's `/v1/chat/completions`
4. Response streamed (or returned) to the client

## Configuration

### `.env` variables

```bash
# Enhancement backend
OLLAMA_API_MODE=native
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=deepseek-r1:latest
OLLAMA_TIMEOUT=30

# Client proxy
API_KEYS_CONFIG=configs/api-keys.json
ENHANCEMENT_RULES_CONFIG=configs/enhancement-rules.json
```

### Client setup (VS Code example)

In VS Code `settings.json`:
```json
{
  "chat.models": [{
    "id": "deepseek-r1:latest",
    "provider": "openaiCompatible",
    "url": "http://localhost:9090/v1",
    "apiKey": "sk-prompthub-code-dev001"
  }]
}
```

## Quick Test

```bash
# Test the client proxy (requires bearer token)
curl -s http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-copilot-dev001" | python3 -m json.tool
```

```bash
# Test a chat completion
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-copilot-dev001" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:latest","messages":[{"role":"user","content":"Hello"}]}'
```

```bash
# Test enhancement backend directly (native mode)
curl -s http://localhost:9090/ollama/enhance \
  -H "X-Client-Name: vscode" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain JWT auth"}'
```

## Troubleshooting

**"Connection refused"** — Ensure Ollama is running: `ollama serve`

**"Missing bearer token" (401)** — Add `Authorization: Bearer <token>` header. Tokens are in `api-keys.json`.

**"Invalid API key" (401)** — Token not found in `api-keys.json`. Reload after edits: `POST /v1/api-keys/reload`

**"Model not found"** — Pull the model: `ollama pull deepseek-r1:latest`

**Enhancement not working** — Check that `enhance: true` is set for the token in `api-keys.json` and the `client_name` has a matching entry in `enhancement-rules.json`.

## References

- [Ollama OpenAI Compatibility](https://github.com/ollama/ollama/blob/main/docs/openai.md)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [Enhancement API](api/enhancement.md)
