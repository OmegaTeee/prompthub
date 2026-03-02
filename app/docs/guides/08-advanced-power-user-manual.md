# Advanced Power User Manual

This guide is for users who want to customize PromptHub beyond the basics.

## Advanced Configuration

### Custom Enhancement Models

By default, PromptHub uses lightweight models for prompt enhancement. You can customize this per app.

**Edit `~/.local/share/prompthub/configs/enhancement-rules.json`:**

```json
{
  "default": {
    "model": "gemma3:4b",
    "system_prompt": null,
    "timeout": 120
  },
  "clients": {
    "my-technical-app": {
      "model": "qwen2.5-coder:32b",
      "system_prompt": "You are a technical expert. Enhance prompts for code quality.",
      "timeout": 180
    },
    "my-creative-app": {
      "model": "gemma3:27b",
      "system_prompt": "You are a creative writer. Enhance prompts for literary quality.",
      "timeout": 120
    },
    "my-fast-app": {
      "model": "gemma3:4b",
      "system_prompt": null,
      "enabled": false
    }
  }
}
```

**Key options:**
- `model` — Which Ollama model to use for enhancement
- `system_prompt` — Custom instructions for enhancement (optional)
- `timeout` — How long to wait before giving up (seconds)
- `enabled` — Can disable enhancement per client

**Available models in Ollama:**
- `gemma3:4b` — Fast (1-2s), good enough
- `gemma3:27b` — Powerful, slower (3-5s)
- `qwen2.5-coder:32b` — Code-specific, very powerful
- `mistral:latest` — Fast and capable
- `llama3:27b` — General purpose, balanced

Pull new models:
```bash
ollama pull qwen2.5-coder:32b
```

---

### API Key Management

#### Creating Fine-Grained API Keys

Instead of one key per app, create multiple keys with different settings:

```json
{
  "keys": {
    "sk-production-001": {
      "client_name": "vscode",
      "enhance": true,
      "description": "Production VS Code"
    },
    "sk-testing-001": {
      "client_name": "vscode",
      "enhance": false,
      "description": "Testing/experimentation"
    },
    "sk-claude-001": {
      "client_name": "claude-desktop",
      "enhance": true,
      "description": "Claude with enhancement"
    }
  }
}
```

Benefits:
- Different enhancement settings per use case
- Can disable one key without affecting others
- Easier to track which key is used where

#### Key Rotation

To safely rotate a key without downtime:

1. Create a new key in `api-keys.json`
2. Update your apps to use the new key
3. Reload keys: `curl -X POST http://localhost:9090/v1/api-keys/reload`
4. Remove old key from `api-keys.json`
5. Reload again

---

### Custom Enhancement Rules

#### Per-Client Timeouts

For slow models, increase the timeout:

```json
{
  "clients": {
    "slow-client": {
      "model": "mistral:large",
      "timeout": 300
    }
  }
}
```

#### Disabling Enhancement for Specific Scenarios

Disable enhancement for a specific API key:

```json
{
  "keys": {
    "sk-fast-only": {
      "client_name": "fast-app",
      "enhance": false
    }
  }
}
```

---

### Memory Advanced Features

#### Semantic Search

Coming in future version — ability to search facts by meaning rather than exact text.

#### Memory Expiration Policies

Automatically expire old facts:

```bash
# Delete facts older than 30 days
curl -X POST http://localhost:9090/sessions/{id}/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

#### Batch Operations

Add multiple facts at once:

```bash
curl -X POST http://localhost:9090/sessions/{id}/facts/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"fact": "Fact 1", "tags": ["tag1"]},
    {"fact": "Fact 2", "tags": ["tag2"]}
  ]'
```

---

## Environment Variables

Fine-tune PromptHub behavior via `.env`:

```bash
# API Configuration
OLLAMA_API_MODE=openai              # or "native"
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_TIMEOUT=120

# Enhancement
AUTO_ENHANCE_MCP=true
ENHANCEMENT_TIMEOUT=180

# API Keys
API_KEYS_CONFIG=configs/api-keys.json
ENHANCEMENT_RULES_CONFIG=configs/enhancement-rules.json

# Memory
MEMORY_DB_PATH=~/.prompthub/memory.db
MEMORY_MCP_ENABLED=false

# Logging
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/router-stderr.log

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=9090
WORKERS=4                            # Number of worker processes

# Performance
CACHE_ENABLED=true
CACHE_TTL=300                        # Cache timeout in seconds
CIRCUIT_BREAKER_ENABLED=true
```

---

## Performance Tuning

### Running Multiple Workers

For high throughput, run multiple worker processes:

```bash
uvicorn router.main:app --workers 4 --host 127.0.0.1 --port 9090
```

This allows 4 concurrent requests. Increase for higher throughput (1 worker per CPU core recommended).

### Caching

Enable response caching for identical requests:

```bash
# In .env
CACHE_ENABLED=true
CACHE_TTL=300
```

Caches responses for 5 minutes. Useful for:
- Repeated prompts
- Multi-app queries (same question asked by different apps)
- Enhancement results (same prompt enhanced multiple times)

### Circuit Breaker

Automatically stop sending requests to failing services:

```bash
# In .env
CIRCUIT_BREAKER_ENABLED=true
```

If Ollama crashes:
- First failure: try once more
- Second failure: disable temporarily
- After 60s: try again gradually
- Once responsive: resume normal operation

---

## Monitoring & Debugging

### Verbose Logging

Enable debug logging:

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Or start PromptHub with logging
uvicorn router.main:app --log-level debug
```

Debug logs show:
- Every request received
- Every external call made
- Cache hits/misses
- Enhancement details
- Circuit breaker state

### Real-Time Log Monitoring

Watch logs as they happen:

```bash
tail -f ~/.local/share/prompthub/logs/router-stderr.log
```

Filter by severity:
```bash
tail -f ~/.local/share/prompthub/logs/router-stderr.log | grep ERROR
tail -f ~/.local/share/prompthub/logs/router-stderr.log | grep WARNING
```

### Metrics & Health

Check system metrics:

```bash
# Health endpoint
curl http://localhost:9090/health

# Detailed metrics
curl http://localhost:9090/metrics

# Memory stats
curl http://localhost:9090/sessions/stats
```

### Profiling

To profile PromptHub (find slow operations):

```bash
# Start with profiler
python -m cProfile -s cumtime -m uvicorn router.main:app --port 9090
```

Look for functions consuming the most time.

---

## Custom MCP Server Integration

### Adding Your Own MCP Server

If you have a custom MCP server, integrate it with PromptHub:

1. Start your MCP server on a different port
2. Configure PromptHub to route to it
3. Access it via PromptHub

**Example: Adding Context7**

```bash
# Terminal 1: Start Context7
context7 serve --port 8000

# Terminal 2: Start PromptHub (it discovers Context7)
cd ~/.local/share/prompthub
uvicorn router.main:app --host 127.0.0.1 --port 9090
```

PromptHub should automatically discover and proxy Context7.

### Custom Tool Development

Build your own tools and expose them via PromptHub:

```python
# my_tool.py
from prompthub.mcp import Tool

class MyCustomTool(Tool):
    def __init__(self):
        self.name = "my-tool"
        self.description = "Does something useful"

    def execute(self, params):
        return {
            "result": f"Processed: {params}"
        }

# Register with PromptHub
if __name__ == "__main__":
    tool = MyCustomTool()
    tool.register()
```

---

## Automation & Integration

### Bash Script Integration

Automate PromptHub calls:

```bash
#!/bin/bash
# prompthub-helper.sh

API_KEY="sk-prompthub-code-001"
BASE_URL="http://localhost:9090"

function ask() {
    local prompt="$1"
    local model="${2:-gemma3:27b}"

    curl -s "$BASE_URL/v1/chat/completions" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}]
        }" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
}

function session_create() {
    local client_id="$1"
    curl -s -X POST "$BASE_URL/sessions" \
        -H "Content-Type: application/json" \
        -d "{\"client_id\": \"$client_id\"}" | python3 -m json.tool
}

function fact_add() {
    local session_id="$1"
    local fact="$2"
    curl -s -X POST "$BASE_URL/sessions/$session_id/facts" \
        -H "Content-Type: application/json" \
        -d "{\"fact\": \"$fact\", \"tags\": [\"auto\"]}"
}

# Usage examples
ask "Explain quantum computing"
session_create "my-app"
```

### Cron Jobs

Schedule PromptHub tasks:

```bash
# Cleanup old sessions (monthly)
0 0 1 * * /usr/local/bin/prompthub-cleanup.sh

# Refresh API keys (never, but keep script for manual use)
# 0 * * * * curl -X POST http://localhost:9090/v1/api-keys/reload
```

---

## Troubleshooting Advanced Issues

### "Enhancement service crashed"

Check logs:
```bash
grep "enhancement" ~/.local/share/prompthub/logs/router-stderr.log
```

If Ollama crashed:
```bash
# Restart Ollama
killall ollama
sleep 2
ollama serve &
```

### "Circuit breaker keeps triggering"

Indicates Ollama is flaky. Either:
1. Increase timeouts: `OLLAMA_TIMEOUT=300` in `.env`
2. Increase Ollama's resources
3. Reduce concurrent requests

### "High memory usage"

Monitor:
```bash
# See memory usage
ps aux | grep ollama
ps aux | grep uvicorn

# Check which models are loaded
ollama list | grep "SIZE"
```

Free up memory:
```bash
# Unload unused models
ollama rm gemma3:4b
```

---

## API Contract (Developer Reference)

### Request/Response Models

All models are Pydantic and validate input/output.

**Session Model:**
```python
{
    "id": "uuid",
    "client_id": "string",
    "created_at": "ISO8601",
    "last_accessed": "ISO8601",
    "status": "active|closed",
    "fact_count": 0
}
```

**Fact Model:**
```python
{
    "id": "uuid",
    "session_id": "uuid",
    "fact": "string",
    "tags": ["string"],
    "relevance_score": 0.0-1.0,
    "source": "manual|inferred|mcp"
}
```

### Error Responses

```json
{
    "detail": "Human-readable error message"
}
```

HTTP Status Codes:
- 200 — Success
- 400 — Bad request format
- 401 — Unauthorized (bad API key)
- 404 — Resource not found
- 500 — Server error

---

## Contributing & Custom Features

### Building Custom Extensions

PromptHub is open source. You can:
1. Fork the repository
2. Add custom features
3. Submit pull requests
4. Run locally in development mode

**Development setup:**
```bash
cd ~/.local/share/prompthub/app
python -m pip install -e ".[dev]"
pytest tests/ -v
```

---

## Performance Benchmark

Typical request times (on M2 Mac):

| Operation | Time |
|-----------|------|
| Health check | 5ms |
| List models | 20ms |
| Enhancement (4b model) | 1-2s |
| Chat completion (4b model) | 2-3s |
| Chat completion (27b model) | 5-10s |
| Session create | 10ms |
| Add fact | 15ms |
| Memory block upsert | 20ms |

---

## Best Practices Summary

✅ DO:
- Use multiple API keys for different use cases
- Enable enhancement for quality-critical tasks
- Monitor memory.db file size regularly
- Use debug logging when troubleshooting
- Keep Ollama and PromptHub updated

❌ DON'T:
- Use extremely large models unless necessary
- Run many models simultaneously
- Commit API keys to version control
- Leave debug logging on permanently (uses disk space)
- Ignore circuit breaker warnings (means system is unstable)

---

**Advanced users:** You now have full control of PromptHub. Experiment, customize, and optimize for your workflow!

For questions, check logs first, then consult the troubleshooting guide.
