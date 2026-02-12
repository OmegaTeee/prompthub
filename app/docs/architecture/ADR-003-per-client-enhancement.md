# ADR-003: Per-Client Prompt Enhancement Rules

## Status
Accepted

## Context
AgentHub routes prompts to Ollama for enhancement before sending to LLMs. Different clients (Claude Desktop, VS Code, Raycast, Obsidian) have different use cases and require different enhancement strategies.

### Problem Statement
A one-size-fits-all approach doesn't work:
- **Claude Desktop** users want structured reasoning and planning
- **VS Code** developers want code-focused, concise responses
- **Raycast** users want action-oriented, quick answers
- **Obsidian** users want markdown-formatted, knowledge-base content

### Requirements
- Support different Ollama models per client
- Customize system prompts for each use case
- Configure temperature and token limits
- Ability to disable enhancement per client
- Maintain backward compatibility (default behavior)

## Decision
Implement **per-client enhancement rules** via configuration file with header-based routing.

### Configuration Format
```json
{
  "rules": {
    "claude-desktop": {
      "enabled": true,
      "model": "deepseek-r1:latest",
      "system_prompt": "You are an expert reasoning assistant. Break down complex problems step-by-step. Focus on clarity and logical structure.",
      "temperature": 0.3,
      "max_tokens": 1000
    },
    "vscode": {
      "enabled": true,
      "model": "qwen2.5-coder:7b",
      "system_prompt": "You are a code-focused assistant. Be concise, technical, and actionable. Prioritize code examples over explanations.",
      "temperature": 0.2,
      "max_tokens": 500
    },
    "raycast": {
      "enabled": true,
      "model": "deepseek-r1:latest",
      "system_prompt": "You are an action-oriented assistant. Provide quick, practical answers. Focus on what to do next.",
      "temperature": 0.3,
      "max_tokens": 300
    },
    "obsidian": {
      "enabled": true,
      "model": "deepseek-r1:latest",
      "system_prompt": "You are a knowledge management assistant. Format responses in clean Markdown. Structure information hierarchically.",
      "temperature": 0.4,
      "max_tokens": 800
    }
  },
  "default": {
    "enabled": true,
    "model": "llama3.2:3b",
    "system_prompt": "Improve clarity and structure. Preserve intent. Return only the enhanced prompt.",
    "temperature": 0.3,
    "max_tokens": 500
  }
}
```

### Client Identification
Clients identify themselves via HTTP header:
```bash
POST /ollama/enhance
X-Client-Name: claude-desktop

{
  "prompt": "Help me write a Python web scraper"
}
```

## Rationale

### Why Per-Client Rules?
✅ **Use-case optimization** - Tailor enhancement to specific workflows
✅ **Model selection** - Use specialized models (code models for VS Code)
✅ **Token efficiency** - Shorter responses for quick-answer clients (Raycast)
✅ **Quality improvement** - Better results from specialized prompts
✅ **User control** - Clients can disable enhancement if not wanted

### Why Header-Based Routing?
✅ **Simple** - No authentication required
✅ **Explicit** - Client declares identity
✅ **Stateless** - No session management
✅ **Backward compatible** - Falls back to default if header missing

### Why JSON Config File?
✅ **Hot reload** - Update rules without restarting
✅ **Version control** - Track changes in git
✅ **Easy editing** - No code changes needed
✅ **Validation** - Pydantic schemas enforce correctness

## Consequences

### Positive
- Clients get optimized enhancement for their use case
- Easy to add new clients (just add config entry)
- A/B testing possible (swap models per client)
- Can disable problematic enhancements per client

### Negative
- Clients can spoof X-Client-Name header (but local-only, trusted)
- Config file can become large with many clients
- Need to maintain multiple system prompts

### Neutral
- Requires clients to set header (documentation)
- Default fallback ensures backward compatibility

## Implementation

### Service Layer
```python
class EnhancementService:
    def __init__(self, rules_path: str):
        self._rules = self._load_rules(rules_path)
        self._default_rule = self._rules.get("default")

    async def enhance(
        self,
        prompt: str,
        client_name: str | None = None,
    ) -> EnhancementResult:
        # Select rule based on client
        rule = self._rules.get(client_name) or self._default_rule

        if not rule.enabled:
            return EnhancementResult(
                original=prompt,
                enhanced=prompt,
                cached=False,
            )

        # Enhance with client-specific config
        enhanced = await self._ollama.generate(
            prompt=prompt,
            model=rule.model,
            system_prompt=rule.system_prompt,
            temperature=rule.temperature,
            max_tokens=rule.max_tokens,
        )

        return EnhancementResult(
            original=prompt,
            enhanced=enhanced,
            model=rule.model,
            cached=False,
        )
```

### FastAPI Endpoint
```python
@app.post("/ollama/enhance")
async def enhance_prompt(
    body: EnhanceRequest,
    x_client_name: str | None = Header(None, alias="X-Client-Name"),
):
    result = await enhancement_service.enhance(
        prompt=body.prompt,
        client_name=x_client_name,
    )
    return result
```

## Model Selection Rationale

### Claude Desktop: deepseek-r1
- **Why**: Best at structured reasoning and step-by-step thinking
- **Size**: 1.3B parameters (fast inference)
- **Speed**: ~500ms for typical prompt

### VS Code: qwen2.5-coder
- **Why**: Code-specialized model with strong instruction following
- **Size**: 7B parameters (good quality/speed balance)
- **Speed**: ~800ms for code generation

### Raycast: deepseek-r1
- **Why**: Fast, action-oriented responses
- **Size**: Small model for quick inference
- **Speed**: ~300ms for short prompts

### Obsidian: deepseek-r1
- **Why**: Good at structured text, markdown formatting
- **Size**: Medium model for quality
- **Speed**: ~600ms typical

### Default: llama3.2
- **Why**: General-purpose, widely available
- **Size**: 3B parameters (good fallback)
- **Speed**: ~400ms typical

## Alternatives Considered

### 1. URL Path Based Routing
```
POST /ollama/enhance/claude-desktop
POST /ollama/enhance/vscode
```

**Rejected** because:
- More API endpoints to maintain
- Client must know available paths
- Harder to add new clients dynamically

**When better**: If authentication is added (different API keys per client)

### 2. Request Body Parameter
```json
{
  "prompt": "...",
  "client_name": "vscode"
}
```

**Rejected** because:
- Mixes routing info with request data
- Headers are standard for metadata
- Less clean separation of concerns

**When better**: If client name needs to be part of cache key

### 3. Environment Variables
```bash
CLAUDE_DESKTOP_MODEL=deepseek-r1
VSCODE_MODEL=qwen3-coder
```

**Rejected** because:
- No hot reload (requires restart)
- Hard to manage many clients
- No structured validation

**When better**: For deployment-specific overrides (Kubernetes ConfigMaps)

### 4. Database Configuration
**Deferred** because:
- Overkill for current scale (~5 clients)
- Adds dependency and complexity
- File-based is sufficient

**When needed**: If rules need to be edited via admin UI, or > 50 clients

## Testing Strategy

### Unit Tests
```python
def test_client_routing():
    service = EnhancementService(rules_path)

    # Claude Desktop gets deepseek-r1
    result = await service.enhance("test", client_name="claude-desktop")
    assert result.model == "deepseek-r1:latest"

    # VS Code gets qwen3-coder
    result = await service.enhance("test", client_name="vscode")
    assert result.model == "qwen2.5-coder:7b"

    # Unknown client gets default
    result = await service.enhance("test", client_name="unknown")
    assert result.model == "llama3.2:3b"
```

### Integration Tests
- Send request with X-Client-Name header
- Verify correct model selected
- Verify system prompt applied
- Verify temperature and token limits

## Monitoring

### Metrics by Client
- Enhancement requests per client
- Average latency per client
- Cache hit rate per client
- Model usage distribution

### Alerts
- High latency for specific client → Model too large?
- Low cache hit rate → Prompts too varied?
- Enhancement failures → Model unavailable?

## Migration Path

### Phase 1: Add header support (backward compatible)
- Accept X-Client-Name but don't require it
- Default rule applies if header missing
- Existing clients continue working

### Phase 2: Client adoption
- Update Claude Desktop config
- Update VS Code integration
- Update Raycast script
- Documentation for custom clients

### Phase 3: Monitor and optimize
- Measure quality improvements
- Adjust system prompts based on feedback
- Fine-tune temperature and token limits

## Related
- [ADR-005: Async-First Architecture](ADR-005-async-first.md) - Enables concurrent enhancements
- [guides/app-configs.md](../../guides/app-configs.md) - Client configuration examples

## References
- [Ollama API Documentation](https://ollama.ai/docs/api)
- [DeepSeek R1 Model Card](https://huggingface.co/deepseek-ai/deepseek-r1)
- [Qwen2.5-Coder](https://huggingface.co/Qwen/Qwen2.5-Coder-7B)

## Revision History
- 2025-01-25: Initial implementation
- 2025-02-02: Documented as ADR
