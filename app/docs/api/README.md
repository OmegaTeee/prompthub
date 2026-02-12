# API Documentation

Comprehensive API reference for AgentHub Router.

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
Currently no authentication required (local-only). For production deployments, use:
```bash
export API_KEY_REQUIRED=true
export API_KEY=your-secret-key
```

Then include in requests:
```bash
curl -H "X-API-Key: your-secret-key" http://localhost:9090/servers
```

## Common Workflows

### 1. Install and Start an MCP Server

```bash
# Install
curl -X POST http://localhost:9090/servers/install \
  -H "Content-Type: application/json" \
  -d '{
    "package": "@modelcontextprotocol/server-memory",
    "name": "memory",
    "auto_start": true
  }'

# Start
curl -X POST http://localhost:9090/servers/memory/start

# Verify
curl http://localhost:9090/health/memory
```

### 2. Enhance a Prompt

```bash
curl -X POST http://localhost:9090/ollama/enhance \
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
  "model": "deepseek-r1:latest",
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

# Specific server
curl http://localhost:9090/health/context7 | jq

# Circuit breaker states
curl http://localhost:9090/circuit-breakers | jq

# Activity log
curl "http://localhost:9090/audit/activity?limit=10" | jq
```

### 5. Generate Client Configurations

```bash
# Claude Desktop
curl http://localhost:9090/configs/claude-desktop > ~/Library/Application\\ Support/Claude/claude_desktop_config.json

# VS Code
curl http://localhost:9090/configs/vscode > .vscode/mcp.json

# Raycast
curl http://localhost:9090/configs/raycast > ~/raycast-mcp.sh
chmod +x ~/raycast-mcp.sh
```

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

**Solution:** Wait for `retry_after` seconds or manually reset:
```bash
curl -X POST http://localhost:9090/circuit-breakers/fetch/reset
```

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

### Ollama Not Available
```json
{
  "original": "your prompt",
  "enhanced": "your prompt",
  "model": null,
  "cached": false,
  "was_enhanced": false,
  "error": "Connection refused: Ollama not available"
}
```

**Solution:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

## WebSocket Support (Future)

Currently all MCP servers use stdio transport. WebSocket support planned for Phase 4.

## Rate Limiting (Future)

No rate limiting currently implemented. For production:
- Implement rate limiting middleware
- Use Redis for distributed rate limiting
- Configure per-client limits in `configs/enhancement-rules.json`

## Versioning

API versioning via URL path:
- `/v1/servers` - Version 1 (future)
- `/servers` - Unversioned (current)

## SDKs

### Python
```python
import httpx

class AgentHubClient:
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
            f"{self.base_url}/ollama/enhance",
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
class AgentHubClient {
  constructor(private baseUrl: string = "http://localhost:9090") {}

  async enhancePrompt(
    prompt: string,
    clientName: string = "vscode",
    bypassCache: boolean = false
  ) {
    const response = await fetch(`${this.baseUrl}/ollama/enhance`, {
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
# Run integration tests
pytest tests/integration/ -v

# Test specific endpoint
pytest tests/integration/test_servers.py::test_list_servers -v

# Load testing with locust
locust -f tests/load/locustfile.py --host http://localhost:9090
```

## Further Reading

- [MCP Protocol Spec](https://modelcontextprotocol.io/docs/specification)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
