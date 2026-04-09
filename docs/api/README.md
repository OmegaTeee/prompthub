# API Documentation

Comprehensive API reference for PromptHub Router.

## OpenAPI Specification

See [openapi.yaml](openapi.yaml) for the complete OpenAPI 3.0 specification.

### Viewing the Spec

**Online Tools:**
- [Swagger Editor](https://editor.swagger.io/) - Paste the YAML content
- [Redocly](https://redocly.github.io/redoc/) - Beautiful API docs

**Local Tools:**
```bash
# Install swagger-ui-watcher
npm install -g swagger-ui-watcher

# Serve the spec
swagger-ui-watcher docs/api/openapi.yaml
```

**VS Code Extension:**
- Install [OpenAPI (Swagger) Editor](https://marketplace.visualstudio.com/items?itemName=42Crunch.vscode-openapi)
- Right-click `openapi.yaml` → "Preview Swagger"

## Quick Reference

### Base URL
```
http://localhost:9090
```

### Authentication
- **MCP proxy, health, servers**: No authentication required (local-only)
- **OpenAI-compatible `/v1/` endpoints**: Bearer token required (configured in `app/configs/api-keys.json`)

```bash
# /v1/ endpoints require a bearer token
curl -H "Authorization: Bearer sk-prompthub-code-001" http://localhost:9090/v1/models
```

## Common Workflows

### 1. Start an MCP Server

```bash
# Start a configured server
curl -X POST http://localhost:9090/servers/memory/start

# Verify
curl http://localhost:9090/health | jq '.servers.memory'
```

### 2. Enhance a Prompt

```bash
curl -X POST http://localhost:9090/llm/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: claude-desktop" \
  -d '{
    "prompt": "Write a Python function to merge two sorted arrays",
    "bypass_cache": false
  }'
```

Response:
```json
{
  "original": "Write a Python function to merge two sorted arrays",
  "enhanced": "Create a Python function that efficiently merges two pre-sorted arrays into a single sorted array. The function should:\n- Accept two sorted lists as parameters\n- Return a new sorted list containing all elements\n- Maintain O(n+m) time complexity\n- Include type hints and docstring",
  "model": "qwen3-4b-instruct-2507",
  "cached": false,
  "was_enhanced": true,
  "error": null
}
```

### 3. Proxy JSON-RPC to MCP Server

```bash
# Fetch documentation via context7
curl -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "query-docs",
      "arguments": {
        "library": "fastapi",
        "query": "dependency injection"
      }
    },
    "id": 1
  }'
```

### 4. Monitor System Health

```bash
# Overall health
curl http://localhost:9090/health | jq

# Circuit breaker states (included in health response)
curl http://localhost:9090/health | jq '.circuit_breakers'

# Activity log
curl "http://localhost:9090/audit/activity?limit=10" | jq

# Dashboard (browser)
open http://localhost:9090/dashboard
```

### 5. Configure a Client

```bash
# Inspect repo-managed client files
ls clients/claude
ls clients/raycast
ls clients/vscode

# Run the client's setup helper when available
./clients/raycast/setup.sh
./clients/claude/desktop-setup.sh
```

PromptHub no longer serves generated client configs from `/configs/*`. Use the
tracked files in `clients/` instead.

## Error Handling

### Circuit Breaker Open
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Server fetch circuit breaker open",
    "data": {
      "retry_after": 25.3
    }
  },
  "id": null
}
```

**Solution:** Wait for `retry_after` seconds. Circuit breakers auto-recover after the recovery timeout (30s default).

### Server Not Running
```json
{
  "detail": "Server context7 is not running"
}
```

**Solution:**
```bash
# Check if auto_start is enabled
curl http://localhost:9090/servers/context7 | jq .config.auto_start

# Start manually
curl -X POST http://localhost:9090/servers/context7/start
```

### LLM Server Not Available
```json
{
  "original": "your prompt",
  "enhanced": "your prompt",
  "model": null,
  "cached": false,
  "was_enhanced": false,
  "error": "Connection refused: LLM server not available"
}
```

**Solution:**
```bash
# Check LM Studio status
curl http://localhost:1234/v1/models

# Start LM Studio and load the enhancement model (qwen3-4b-instruct-2507)
```

## Versioning

The `/v1/` prefix is used for the OpenAI-compatible proxy endpoints. All other endpoints are unversioned.

## SDKs

### Python
```python
import httpx

class PromptHubClient:
    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def enhance_prompt(
        self,
        prompt: str,
        client_name: str = "claude-desktop",
        bypass_cache: bool = False
    ):
        response = await self.client.post(
            f"{self.base_url}/llm/enhance",
            json={"prompt": prompt, "bypass_cache": bypass_cache},
            headers={"X-Client-Name": client_name}
        )
        return response.json()

    async def list_servers(self):
        response = await self.client.get(f"{self.base_url}/servers")
        return response.json()
```

### TypeScript
```typescript
class PromptHubClient {
  constructor(private baseUrl: string = "http://localhost:9090") {}

  async enhancePrompt(
    prompt: string,
    clientName: string = "vscode",
    bypassCache: boolean = false
  ) {
    const response = await fetch(`${this.baseUrl}/llm/enhance`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Client-Name": clientName,
      },
      body: JSON.stringify({ prompt, bypass_cache: bypassCache }),
    });
    return response.json();
  }

  async listServers() {
    const response = await fetch(`${this.baseUrl}/servers`);
    return response.json();
  }
}
```

## Testing the API

```bash
# Run integration tests (from app/ directory)
cd app && pytest tests/integration/ -v

# Run unit tests
cd app && pytest tests/unit/ -v
```

## Further Reading

- [Glossary](../glossary.md) — Canonical definitions for project terminology (router, bridge, proxy, enhancement, etc.)
- [MCP Protocol Spec](https://modelcontextprotocol.io/docs/specification)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
