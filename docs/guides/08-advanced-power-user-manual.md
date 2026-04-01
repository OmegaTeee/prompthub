# Advanced Power User Manual

This guide is for users who want to customize PromptHub beyond the basics. It covers custom models, API keys, performance tuning, monitoring, scripting, and troubleshooting.

---

## Custom Enhancement Models

PromptHub uses lightweight models to rewrite your prompts before they reach the AI. You can swap these models per app. Think of it like choosing a different editor for different writing tasks: a quick proofreader for casual chat, a thorough editor for important work.

### How to Configure

Edit `~/prompthub/configs/enhancement-rules.json`:

```json
{
  "default": {
    "model": "qwen/qwen3-4b-2507",
    "system_prompt": null,
    "timeout": 120
  },
  "clients": {
    "my-technical-app": {
      "model": "qwen/qwen3-4b-2507",
      "system_prompt": "You are a technical expert. Enhance prompts for code quality.",
      "timeout": 180
    },
    "my-creative-app": {
      "model": "qwen/qwen3-4b-2507",
      "system_prompt": "You are a creative writer. Enhance prompts for literary quality.",
      "timeout": 120
    },
    "my-fast-app": {
      "model": "qwen/qwen3-4b-2507",
      "system_prompt": null,
      "enabled": false
    }
  }
}
```

### Configuration Options

| Option | What it does |
|--------|-------------|
| `model` | Which LM Studio model to use for enhancement |
| `system_prompt` | Custom instructions that guide how enhancement works (optional) |
| `timeout` | How many seconds to wait before giving up |
| `enabled` | Set to `false` to turn off enhancement for a specific client |

### Current Enhancement Model

All clients now use the same model for enhancement:

| Model | Speed | Strength |
|-------|-------|----------|
| `qwen/qwen3-4b-2507` | Fast (1-2 seconds) | Good for all enhancement tasks |

To download the model:

```bash
lms get qwen/qwen3-4b-2507
```

**Key points:**
- All clients share the same enhancement model (`qwen/qwen3-4b-2507`).
- Per-client entries let you customize the system prompt, timeout, or disable enhancement.
- Set `enabled: false` to skip enhancement for apps that do not need it.

---

## API Key Management

API keys control which apps can access PromptHub. Think of them like keycards for a building: each card can open different doors with different permissions.

### Creating Fine-Grained API Keys

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

**Benefits:**
- Different enhancement settings per use case.
- You can disable one key without affecting others.
- Easier to track which key is used where.

### Key Rotation

To rotate a key without downtime, follow these steps:

1. Add a new key to `api-keys.json`.
2. Update your apps to use the new key.
3. Reload the key list:
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```
4. Remove the old key from `api-keys.json`.
5. Reload again:
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```

**Key points:**
- Use separate keys for production and testing.
- Rotate keys by adding the new one first, then removing the old one.
- Reload after every change so PromptHub picks up the updated keys.

---

## Custom Enhancement Rules

### Per-Client Timeouts

Some models take longer to respond. Increase the timeout for slow models so PromptHub does not give up too soon:

```json
{
  "clients": {
    "slow-client": {
      "model": "qwen/qwen3-4b-2507",
      "timeout": 300
    }
  }
}
```

### Disabling Enhancement for Specific Keys

Turn off enhancement for a specific API key. This is useful when you want raw, unmodified responses:

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

## Memory Advanced Features

The memory system stores facts and context across conversations. Think of it like a notebook that PromptHub keeps beside every conversation.

### Semantic Search

Coming in a future version. This will let you search facts by meaning rather than exact text.

### Memory Expiration

Old facts can pile up. Clean them out automatically:

```bash
# Delete facts older than 30 days
curl -X POST http://localhost:9090/sessions/{id}/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

Replace `{id}` with your session ID.

### Batch Operations

Add multiple facts at once instead of one at a time:

```bash
curl -X POST http://localhost:9090/sessions/{id}/facts/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"fact": "Fact 1", "tags": ["tag1"]},
    {"fact": "Fact 2", "tags": ["tag2"]}
  ]'
```

**Key points:**
- Clean up old facts regularly to keep the memory database lean.
- Use batch operations when you have many facts to add.
- Replace `{id}` with your actual session ID in all commands.

---

## Environment Variables

You can fine-tune PromptHub's behavior by editing the `.env` file. Think of these as dials and switches that control how the system runs under the hood.

```bash
# API Configuration
LLM_HOST=localhost
LLM_PORT=1234
LLM_TIMEOUT=120

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

**Key points:**
- `LLM_TIMEOUT` controls how long PromptHub waits for LM Studio before giving up.
- `CACHE_TTL` sets how many seconds cached responses stay valid.
- `LOG_LEVEL` at `DEBUG` gives the most detail; `INFO` is the normal setting.

---

## Performance Tuning

### Running Multiple Workers

By default, PromptHub handles one request at a time. For higher throughput, run multiple worker processes. This is like opening more checkout lanes at a store.

```bash
uvicorn router.main:app --workers 4 --host 127.0.0.1 --port 9090
```

This allows 4 requests to be processed at the same time. A good rule: use 1 worker per CPU core.

### Caching

Caching stores responses so identical requests get instant answers. This saves time and resources when the same question comes up again.

```bash
# In .env
CACHE_ENABLED=true
CACHE_TTL=300
```

This caches responses for 5 minutes (300 seconds). Caching helps with:
- Repeated prompts.
- The same question asked by different apps.
- Enhancement results when the same prompt is enhanced more than once.

### Circuit Breaker

The circuit breaker protects PromptHub from wasting time on a service that is down. Think of it like a real circuit breaker in your house: it trips to prevent damage, then resets when things are safe again.

```bash
# In .env
CIRCUIT_BREAKER_ENABLED=true
```

Here is what happens if LM Studio crashes:
1. First failure: PromptHub tries once more.
2. Second failure: PromptHub temporarily stops sending requests.
3. After 60 seconds: PromptHub tries again cautiously.
4. Once LM Studio responds: Normal operation resumes.

**Key points:**
- More workers means more concurrent requests. Match workers to CPU cores.
- Caching eliminates redundant work for repeated prompts.
- The circuit breaker prevents cascading failures when a service goes down.

---

## Monitoring and Debugging

### Verbose Logging

When something goes wrong, turn on debug logging to see every detail:

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Or start PromptHub with debug logging
uvicorn router.main:app --log-level debug
```

Debug logs show:
- Every request received.
- Every external call made.
- Cache hits and misses.
- Enhancement details.
- Circuit breaker state changes.

> **Warning:** Debug logging writes a lot of data to disk. Turn it off when you are done troubleshooting.

### Real-Time Log Monitoring

Watch logs as they happen:

```bash
tail -f ~/prompthub/logs/router-stderr.log
```

Filter by severity to focus on problems:

```bash
tail -f ~/prompthub/logs/router-stderr.log | grep ERROR
tail -f ~/prompthub/logs/router-stderr.log | grep WARNING
```

### Metrics and Health

Check system metrics with these commands:

```bash
# Health endpoint
curl http://localhost:9090/health

# Detailed metrics
curl http://localhost:9090/metrics

# Memory stats
curl http://localhost:9090/sessions/stats
```

### Profiling

To find slow operations, run PromptHub with Python's built-in profiler:

```bash
python -m cProfile -s cumtime -m uvicorn router.main:app --port 9090
```

This outputs a list of functions sorted by how much time they consume. Look at the top entries to find bottlenecks.

**Key points:**
- Use `DEBUG` logging to investigate problems, then switch back to `INFO`.
- `tail -f` with `grep` lets you watch for specific log levels in real time.
- The profiler helps you find which operations are slowing things down.

---

## Custom MCP Server Integration

### Adding Your Own MCP Server

If you have a custom MCP server, you can route it through PromptHub. This lets all your apps access it through one endpoint.

**Example: Adding Context7**

```bash
# Terminal 1: Start Context7
context7 serve --port 8000

# Terminal 2: Start PromptHub (it discovers Context7)
cd ~/prompthub
uvicorn router.main:app --host 127.0.0.1 --port 9090
```

PromptHub discovers and proxies Context7 automatically.

### Custom Tool Development

Build your own tools and expose them through PromptHub:

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

**Key points:**
- PromptHub can discover and proxy custom MCP servers automatically.
- You can build your own tools and register them with PromptHub.

---

## Automation and Integration

### Bash Script Integration

Automate PromptHub calls from the command line. This script provides helper functions you can reuse:

```bash
#!/bin/bash
# prompthub-helper.sh

API_KEY="sk-prompthub-code-001"
BASE_URL="http://localhost:9090"

function ask() {
    local prompt="$1"
    local model="${2:-qwen/qwen3-4b-2507}"

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

Schedule recurring PromptHub tasks using cron:

```bash
# Cleanup old sessions (monthly, on the 1st at midnight)
0 0 1 * * /usr/local/bin/prompthub-cleanup.sh

# Refresh API keys (manual use only — uncomment if needed)
# 0 * * * * curl -X POST http://localhost:9090/v1/api-keys/reload
```

**Key points:**
- The bash helper functions let you call PromptHub from scripts and the terminal.
- Use cron for recurring maintenance tasks like session cleanup.

---

## Troubleshooting Advanced Issues

### "Enhancement service crashed"

1. Check the logs for clues:
   ```bash
   grep "enhancement" ~/prompthub/logs/router-stderr.log
   ```
1. If LM Studio crashed, restart it:
  ```bash
  lms server stop || true
  sleep 2
  lms server start &
  ```

### "Circuit breaker keeps triggering"

This means LM Studio is struggling to keep up. Try one of these fixes:

1. Increase the timeout in `.env`:
  ```bash
  LM_STUDIO_TIMEOUT=300
  ```
1. Give LM Studio more system resources (close other heavy apps).
1. Reduce the number of concurrent requests.

### "High memory usage"

1. Check what is using memory:
  ```bash
  ps aux | grep lms
  ps aux | grep uvicorn
  ```
1. See which models are loaded:
  ```bash
  lms ls | grep "SIZE"
  ```
1. Unload models you are not using:
  ```bash
  lms rm model-name
  ```

**Key points:**
- Check logs first when something breaks.
- Circuit breaker warnings mean a downstream service is unstable.
- Unload unused LM Studio models to free up memory.

---

## API Contract (Developer Reference)

All request and response models are validated by Pydantic. Pydantic is a data validation library that checks inputs and outputs match the expected format, like a bouncer checking IDs at the door.

### Session Model

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

### Fact Model

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

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request format |
| 401 | Unauthorized (bad API key) |
| 404 | Resource not found |
| 500 | Server error |

---

## Contributing and Custom Features

PromptHub is open source. You can extend it to fit your needs.

1. Fork the repository.
2. Add custom features.
3. Submit pull requests.
4. Run locally in development mode.

**Development setup:**

```bash
cd ~/prompthub/app
python -m pip install -e ".[dev]"
pytest tests/ -v
```

---

## Performance Benchmarks

Typical request times on an M2 Mac:

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

**Do:**
- Use multiple API keys for different use cases.
- Enable enhancement for quality-critical tasks.
- Monitor the `memory.db` file size regularly.
- Use debug logging when troubleshooting.
  - Keep LM Studio and PromptHub updated.

**Do not:**
- Use extremely large models unless you need them.
- Run many models at the same time.
- Commit API keys to version control.
- Leave debug logging on permanently (it fills up disk space).
- Ignore circuit breaker warnings (they mean the system is unstable).

---

You now have full control of PromptHub. Experiment, customize, and optimize for your workflow.

For questions, check the logs first, then consult the Troubleshooting Guide.
