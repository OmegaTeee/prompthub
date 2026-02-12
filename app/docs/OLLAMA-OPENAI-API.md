# Ollama OpenAI-Compatible API Support

AgentHub now supports **both** Ollama API formats:
- **Native Ollama API** (default): `/api/generate`, `/api/tags`
- **OpenAI-Compatible API**: `/v1/chat/completions`, `/v1/models`

## Why Two API Formats?

Ollama exposes OpenAI-compatible endpoints at `/v1/*` allowing drop-in replacement of OpenAI clients. This is useful for:

1. **Compatibility**: Tools built for OpenAI can work with local Ollama
2. **Standardization**: OpenAI format is widely supported
3. **Migration**: Easy to switch between OpenAI and Ollama
4. **Tooling**: Some libraries expect OpenAI format

## Configuration

Set the API mode in your `.env` file:

```bash
# Use native Ollama API (default)
OLLAMA_API_MODE=native

# Or use OpenAI-compatible API
OLLAMA_API_MODE=openai
```

## Implementation Details

### Native API (default)

```python
# Uses /api/generate endpoint
POST http://localhost:11434/api/generate
{
  "model": "llama3.2:3b",
  "prompt": "Hello",
  "system": "You are helpful",
  "options": {
    "temperature": 0.7
  }
}

# Response
{
  "model": "llama3.2:3b",
  "response": "Hi there!",
  "done": true
}
```

### OpenAI-Compatible API

```python
# Uses /v1/chat/completions endpoint
POST http://localhost:11434/v1/chat/completions
{
  "model": "llama3.2:3b",
  "messages": [
    {"role": "system", "content": "You are helpful"},
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7
}

# Response (OpenAI format)
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "llama3.2:3b",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hi there!"
    },
    "finish_reason": "stop"
  }]
}
```

## Code Architecture

### Files Modified/Created

1. **`router/enhancement/ollama_openai.py`** (NEW)
   - `OllamaOpenAIClient` - OpenAI-compatible async client
   - `ChatCompletionResponse` - Response model
   - `OpenAICompatConfig` - Configuration model
   - Error classes: `OllamaOpenAIError`, `OllamaOpenAIConnectionError`

2. **`router/enhancement/service.py`** (MODIFIED)
   - Added dual client support with type narrowing
   - Uses `isinstance()` checks for type-safe API dispatch
   - Unified error handling for both API types

3. **`router/config/settings.py`** (MODIFIED)
   - Added `ollama_api_mode` setting (defaults to "native")

### Type Safety

AgentHub uses Python's union types and `isinstance()` for type narrowing:

```python
class EnhancementService:
    _ollama: OllamaClient | OllamaOpenAIClient

    def __init__(self, ...):
        if settings.ollama_api_mode == "openai":
            self._ollama = OllamaOpenAIClient(...)
        else:
            self._ollama = OllamaClient(...)

    async def enhance(self, ...):
        if isinstance(self._ollama, OllamaOpenAIClient):
            # Type narrowed to OllamaOpenAIClient
            enhanced = await self._ollama.generate_from_prompt(...)
        else:
            # Type narrowed to OllamaClient
            response = await self._ollama.generate(...)
            enhanced = response.response.strip()
```

## Switching Between APIs

### At Startup

Set environment variable:
```bash
export OLLAMA_API_MODE=openai
uvicorn router.main:app --port 9090
```

### Runtime Behavior

- Circuit breaker works with both APIs
- Caching works identically for both
- Error handling unified across both APIs
- Performance characteristics similar

## Performance Comparison

Both APIs have similar performance:

| Metric | Native API | OpenAI API |
|--------|-----------|------------|
| First request | ~2-3s | ~2-3s |
| Cached request | <500ms | <500ms |
| Network overhead | Minimal | Minimal |
| Model loading | Same | Same |

## Testing

### Manual Testing

```bash
# Test native API
curl http://localhost:11434/api/generate \
  -d '{"model":"llama3.2:3b","prompt":"Hello"}'

# Test OpenAI-compatible API
curl http://localhost:11434/v1/chat/completions \
  -d '{"model":"llama3.2:3b","messages":[{"role":"user","content":"Hello"}]}'
```

### Automated Testing

```bash
# Run integration tests (tests both modes if Ollama is running)
./scripts/run-tests.sh integration

# Or with pytest
pytest tests/integration/test_enhancement_and_caching.py -v
```

## Troubleshooting

### Error: "Connection refused"

Ensure Ollama is running:
```bash
ollama serve
```

### Error: "Model not found"

List available models:
```bash
# Native API
curl http://localhost:11434/api/tags

# OpenAI API
curl http://localhost:11434/v1/models
```

Pull the model if needed:
```bash
ollama pull llama3.2:3b
```

### Switching modes not working

1. Check `.env` file:
   ```bash
   cat .env | grep OLLAMA_API_MODE
   ```

2. Restart AgentHub:
   ```bash
   uvicorn router.main:app --reload --port 9090
   ```

3. Verify in logs:
   ```
   INFO: Using OpenAI-compatible Ollama API
   # or
   INFO: Using native Ollama API
   ```

## When to Use Each API

### Use Native API when:
- ✅ Default setup (no special requirements)
- ✅ Ollama-specific features needed
- ✅ Simpler response format preferred
- ✅ Direct Ollama integration

### Use OpenAI API when:
- ✅ Migrating from OpenAI to Ollama
- ✅ Tools expect OpenAI format
- ✅ Standardized chat message format
- ✅ Cross-platform compatibility

## Future Enhancements

Potential improvements:
- [ ] Add streaming support for both APIs
- [ ] Per-client API mode selection
- [ ] Auto-detect best API based on model
- [ ] Performance benchmarking dashboard

## References

- [Ollama OpenAI Compatibility](https://github.com/ollama/ollama/blob/main/docs/openai.md)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [AgentHub Enhancement Architecture](./ENHANCEMENT.md)

---

**Added**: 2026-01-30
**Version**: 1.0.0
**Status**: ✅ Production Ready
