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
OLLAMA_API_MODE=native   # Uses /api/generate
OLLAMA_API_MODE=openai   # Uses /v1/chat/completions (current setting)
```

Both modes produce identical results — the difference is the wire format. The mode is selected at startup and logged:
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
      "description": "VS Code chat (enhanced)"
    },
    "sk-prompthub-copilot-dev001": {
      "client_name": "vscode",
      "enhance": false,
      "description": "OAI Copilot extension (pass-through)"
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
OLLAMA_API_MODE=openai
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:latest
OLLAMA_TIMEOUT=120

# Client proxy
API_KEYS_CONFIG=configs/api-keys.json
ENHANCEMENT_RULES_CONFIG=configs/enhancement-rules.json
```

### Enhancement rules (`enhancement-rules.json`)

Each client maps to a model used for prompt enhancement. The enhancement model runs *before* the user's requested model. Using a lightweight model (`llama3.2`) for enhancement keeps it fast and avoids model swap overhead:

```json
{
  "default": { "model": "llama3.2:latest" },
  "clients": {
    "vscode":  { "model": "llama3.2:latest" },
    "raycast": { "model": "llama3.2:latest" },
    "obsidian": { "model": "llama3.2:latest" }
  }
}
```

**Model swap warning:** If the enhancement model differs from the chat model, Ollama must
swap models twice per request (load enhancement model → enhance → load chat model →
respond). On single-GPU setups this adds significant latency. To avoid this, use the
same model for both enhancement and chat, or set `"enhance": false` in `api-keys.json`.

### Client setup (VS Code example)

In VS Code `settings.json`:
```json
{
  "chat.models": [{
    "id": "qwen2.5-coder:32b",
    "provider": "openaiCompatible",
    "url": "http://localhost:9090/v1",
    "apiKey": "sk-prompthub-code-dev001"
  }]
}
```

## Quick Test

```bash
# 1. List available models
curl -s http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-copilot-dev001" | python3 -m json.tool
```

```bash
# 2. Chat completion WITHOUT enhancement (pass-through token)
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-copilot-dev001" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:latest","messages":[{"role":"user","content":"Hello"}]}'
```

```bash
# 3. Chat completion WITH enhancement (enhanced token)
#    The last user message is rewritten by the enhancement service
#    before being forwarded to Ollama.
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-code-dev001" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-coder:32b","messages":[{"role":"user","content":"Explain JWT auth"}]}'
```

```bash
# 4. Test enhancement directly via /ollama/enhance
curl -s -X POST http://localhost:9090/ollama/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: vscode" \
  -d '{"prompt":"Explain JWT auth"}' | python3 -m json.tool
```

```bash
# 5. Reload API keys after editing api-keys.json
curl -s -X POST http://localhost:9090/v1/api-keys/reload
```

## Troubleshooting

**"Connection refused"** — Ensure Ollama is running: `ollama serve` or check `launchctl list | grep ollama`.

**"Missing bearer token" (401)** — Add `Authorization: Bearer <token>` header. Tokens are in `api-keys.json`.

**"Invalid API key" (401)** — Token not found in `api-keys.json`. Reload after edits: `POST /v1/api-keys/reload`.

**"Method Not Allowed" (405)** — You're sending GET to a POST-only endpoint. Use `curl -X POST` or `-d '{...}'`.

**"Model not found"** — Pull the model first: `ollama pull llama3.2:latest`. Check available models: `GET /v1/models`.

**Enhancement slow or timing out** — The enhancement service has a 30-second timeout. Large models (`qwen2.5-coder:32b`, `deepseek-r1`) may exceed this if Ollama needs to swap models. Fixes:
- Use the same model for enhancement and chat completion to avoid model swaps
- Set `"enhance": false` for the token in `api-keys.json` to skip enhancement entirely
- Check `tail logs/router-stderr.log` for `Ollama request timed out` warnings

**Enhancement not working** — Verify: (1) `enhance: true` is set for the token in `api-keys.json`, (2) the token's `client_name` has a matching entry in `enhancement-rules.json`, (3) the enhancement model is pulled in Ollama.

## References

- [Ollama OpenAI Compatibility](https://github.com/ollama/ollama/blob/main/docs/openai.md)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
