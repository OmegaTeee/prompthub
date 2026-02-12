# Awesome-Copilot Instructions for AgentHub

Reference for key awesome-copilot instructions integrated with AgentHub development.

## Python Development

### python-mcp-server.instructions.md

**Coverage:** Building MCP servers with FastMCP patterns.

**Key Topics:**

- FastMCP decorators: `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`
- Type hints and Pydantic models
- Async/await patterns
- Error handling
- Context for logging and progress
- Lifespan context managers
- HTTP servers with streamable transport

**Relevance to AgentHub:**

- All new MCP servers must follow these patterns
- Guides implementation of router extensions
- Ensures compatibility with existing MCP infrastructure

**Quick Pattern:**

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"
```

---

### python.instructions.md

**Coverage:** Python coding conventions and best practices.

**Key Topics:**

- PEP 8 compliance
- Type hints for all functions
- Comprehensive docstrings
- Edge case handling
- Clear exception handling

**Relevance to AgentHub:**

- Applied to all Python code in router and MCP servers
- Ensures code quality and maintainability
- Enforces type safety

---

## Containerization & Docker

### containerization-docker-best-practices.instructions.md

**Coverage:** Production-ready Docker practices for building and deploying containers.

**Key Topics:**

- Multi-stage builds (golden rule)
- Minimal base images (Alpine, slim, distroless)
- Layer optimization and ordering
- Non-root user security
- Health checks with HEALTHCHECK directive
- Resource limits and monitoring
- Security scanning (hadolint, Trivy)

**Relevance to AgentHub:**

- AgentHub Dockerfile uses multi-stage builds
- Add health checks to docker-compose.yml
- Integrate security scanning into CI/CD
- Optimize layer ordering for build speed

**Current Dockerfile Status:**

- ✅ Multi-stage build implemented
- ✅ Non-root user configured
- ⏳ Add HEALTHCHECK directive
- ⏳ Integrate hadolint and Trivy scanning

---

## Testing & Quality

### Security and OWASP

**Coverage:** Security best practices and OWASP guidelines.

**Key Topics:**

- Input validation
- Authentication and authorization
- Secrets management
- Error handling without exposing information
- Logging and monitoring
- Dependency scanning

**Relevance to AgentHub:**

- Keyring integration for secrets management
- Input validation in router endpoints
- Audit logging for security events
- Regular security reviews

---

## Code Quality Standards

### Apply These Instructions to All AgentHub Code

1. **python.instructions.md** - All Python files
2. **containerization-docker-best-practices.instructions.md** - Dockerfile and docker-compose
3. **security-and-owasp.instructions.md** - All code, especially security-sensitive areas

---

## Key Requirements from Instructions

### FastMCP (All MCP Servers)

```python
# Type hints are mandatory
@mcp.tool()
def my_tool(param: str, count: int) -> dict[str, Any]:
    """Clear, descriptive docstring."""
    # Implementation
```

### Python Code (All Files)

```python
# Type hints on all functions
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Get data from URL."""
    pass

# Comprehensive docstrings
def complex_logic(a: int) -> str:
    """
    Process the input value.

    Args:
        a: The input integer

    Returns:
        A string representation of the result

    Raises:
        ValueError: If a is negative
    """
    pass
```

### Docker (Dockerfile, docker-compose.yml)

```dockerfile
# Multi-stage build
FROM python:3.11-slim as base
# ... build dependencies ...

FROM python:3.11-slim as runtime
# ... copy built artifacts ...
# Health check
HEALTHCHECK --interval=30s CMD curl -f http://localhost:9090/health || exit 1
```

---

## Integration Checklist

- [ ] Review `python-mcp-server.instructions.md` before implementing MCP servers
- [ ] Check `containerization-docker-best-practices.instructions.md` for Docker improvements
- [ ] Apply `python.instructions.md` standards to all code
- [ ] Reference `security-and-owasp.instructions.md` for security-sensitive code
- [ ] Update linting rules to enforce instruction requirements
- [ ] Include instruction compliance in code review checklist

---

## Related Resources

- [awesome-copilot-recommendations.md](./awesome-copilot-recommendations.md) - Main index
- [agents/awesome-copilot-agents.md](./agents/awesome-copilot-agents.md) - Agent reference
- [prompts/awesome-copilot-generators.md](./prompts/awesome-copilot-generators.md) - Generators
- [copilot-instructions.md](./copilot-instructions.md) - Project guidelines
- [docs/AWESOME-COPILOT-RESOURCES.md](../docs/AWESOME-COPILOT-RESOURCES.md) - Full reference
