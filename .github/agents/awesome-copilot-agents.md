# Recommended Awesome-Copilot Agents for AgentHub

Quick reference for using awesome-copilot expert agents in AgentHub development.

## Core Development Agents

### @python-mcp-expert

**Purpose:** Expert guidance on building MCP servers in Python using FastMCP patterns.

**Use Cases:**

- Implementing new MCP tools with type hints
- Optimizing existing server implementations
- Architecture guidance for MCP servers
- Error handling and validation patterns

**Example Usage:**

```
@python-mcp-expert: How should I implement a new tool for caching
results in the AgentHub router?
```

**Key Context:**

- FastMCP decorators: `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`
- Type hints are mandatory
- Pydantic models for structured output
- Context for logging and progress
- Async/await patterns

---

### @context7

**Purpose:** Access latest library versions and best practices from Context7 documentation.

**Use Cases:**

- Check latest FastAPI patterns
- Verify Pydantic usage
- Get httpx best practices
- Confirm async patterns

**Example Usage:**

```
@context7: What are the best practices for async context managers in Python 3.11?
```

---

### @task-planner

**Purpose:** Break down features into granular, actionable tasks.

**Use Cases:**

- Plan Phase 2.1 (Qdrant cache feature)
- Decompose complex features
- Create implementation checklists
- Identify dependencies

**Example Usage:**

```
@task-planner: Break down the Qdrant L2 cache implementation for AgentHub,
including circuit breaker integration and error handling.
```

---

## Implementation Agents

### @tdd-red, @tdd-green, @tdd-refactor

**Purpose:** TDD workflow agents for test-driven development.

**Red Phase:** Write failing tests first

```
@tdd-red: Write tests for the circuit breaker state transitions
```

**Green Phase:** Implement to pass tests

```
@tdd-green: Implement the circuit breaker to pass the tests
```

**Refactor Phase:** Improve code while tests pass

```
@tdd-refactor: Improve the circuit breaker implementation for performance
```

---

### @implementation-plan

**Purpose:** Create structured roadmaps for implementation.

**Use Cases:**

- Build detailed implementation plans from task breakdowns
- Estimate implementation complexity
- Identify testing strategy
- Plan documentation needs

**Example Usage:**

```
@implementation-plan: Create a detailed implementation plan for the Qdrant cache
based on the task breakdown from @task-planner
```

---

## Architecture & Security Agents

### @se-system-architecture-reviewer

**Purpose:** Review and improve system architecture.

**Use Cases:**

- Evaluate router architecture
- Review cache design
- Assess circuit breaker patterns
- Identify architectural improvements

**Example Usage:**

```
@se-system-architecture-reviewer: Review the current routing architecture
for scalability and resilience patterns
```

---

### @se-security-reviewer

**Purpose:** Security-focused code review.

**Use Cases:**

- Review cache implementation for security
- Identify secrets management patterns
- Assess keyring integration
- Review input validation

**Example Usage:**

```
@se-security-reviewer: Review the cache implementation for potential
security vulnerabilities and best practices
```

---

## Usage Tips

1. **Always provide context:** Include the feature, current state, and constraints
2. **Reference documentation:** Link to relevant docs or code files
3. **Be specific:** Describe the problem clearly before asking for guidance
4. **Follow up:** Ask clarifying questions if the guidance isn't clear
5. **Apply changes:** Test recommendations before merging to main

## Related Resources

- [awesome-copilot-recommendations.md](./awesome-copilot-recommendations.md) - Main index
- [copilot-instructions.md](./copilot-instructions.md) - Project guidelines
- [docs/AWESOME-COPILOT-RESOURCES.md](../docs/AWESOME-COPILOT-RESOURCES.md) - Full reference
