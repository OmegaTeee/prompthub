# Awesome-Copilot Recommendations for AgentHub

This file references the best awesome-copilot resources for AgentHub development.
For full details, see [docs/AWESOME-COPILOT-RESOURCES.md](../docs/AWESOME-COPILOT-RESOURCES.md).

## Recommended Collections

1. **Python MCP Server Development** - Building MCP servers with FastMCP
2. **Containerization & Docker Best Practices** - Multi-stage builds, security, health checks
3. **Testing & Test Automation** - TDD patterns and test automation
4. **Security & Code Quality** - OWASP, accessibility, performance optimization
5. **Project Planning & Management** - Feature decomposition and roadmaps

## Quick Reference: Expert Agents

Use these agents in Copilot Chat by prefixing with `@`:

### Core Development

- `@python-mcp-expert` - MCP server development in Python
- `@context7` - Latest library versions and best practices
- `@task-planner` - Break down features into actionable tasks

### Implementation

- `@implementation-plan` - Create structured roadmaps
- `@tdd-red` - Write failing tests first
- `@tdd-green` - Implement to pass tests
- `@tdd-refactor` - Improve code while tests pass

### Architecture & Security

- `@se-system-architecture-reviewer` - Review architecture decisions
- `@se-security-reviewer` - Security code review

## Quick Reference: Generators & Prompts

Run these generators in VS Code Copilot Chat:

### Project Analysis

- `technology-stack-blueprint-generator` - Document/analyze current architecture
- `architecture-blueprint-generator` - Create comprehensive architecture docs
- `project-workflow-analysis-blueprint-generator` - Document end-to-end workflows

### Code Generation

- `python-mcp-server-generator` - Generate complete MCP server projects
- `multi-stage-dockerfile` - Optimize Docker builds

### Improvements

- `copilot-instructions-blueprint-generator` - Generate/improve copilot-instructions.md
- `performance-optimization` - Identify and fix performance issues

## Usage Examples

### Planning Phase 2.1 (Qdrant Cache)

```
@task-planner Break down the Qdrant L2 cache implementation for AgentHub
```

### Implementing a New MCP Server

```
@python-mcp-expert How should I implement a new tool for X in AgentHub's router?
```

### Security Review

```
@se-security-reviewer Review the cache implementation for security issues
```

### Testing Strategy

```
@tdd-red I need to test the circuit breaker functionality
```

## Installing Resources

To use these resources:

1. **Access awesome-copilot in Copilot Chat**
   - Type `@` followed by agent name
   - Use `/` for generator commands

2. **Reference the Collections**
   - Python MCP: Review `python-mcp-server.instructions.md`
   - Docker: Review `containerization-docker-best-practices.instructions.md`
   - Security: Review `security-and-owasp.instructions.md`

3. **Create Architecture Blueprints**

   ```
   /run technology-stack-blueprint-generator
   /run architecture-blueprint-generator
   ```

4. **Plan Implementation**
   ```
   @task-planner <feature description>
   @implementation-plan <from task breakdown>
   ```

## Key FastMCP Patterns

From `python-mcp-server.instructions.md`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AgentHub Server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

Key requirements:

- Type hints are mandatory
- Pydantic models for structured output
- Use `Context` for logging/progress
- Implement proper error handling

## Next Actions

1. Review `technology-stack-blueprint-generator` against current architecture
2. Implement Docker security scanning (hadolint, Trivy) in CI/CD
3. Plan Phase 2.1 using `@task-planner`
4. Create architecture documentation using `@se-system-architecture-reviewer`
5. Audit security using `@se-security-reviewer`

## Related Files

- [copilot-instructions.md](./copilot-instructions.md) - Project Copilot guidelines
- [docs/AWESOME-COPILOT-RESOURCES.md](../docs/AWESOME-COPILOT-RESOURCES.md) - Full reference
- [Copilot-Processing.md](../Copilot-Processing.md) - Task tracking (root)
