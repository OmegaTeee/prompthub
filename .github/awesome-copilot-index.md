# Awesome-Copilot Resources for AgentHub

Master index of awesome-copilot integration for AgentHub development.

## Quick Navigation

### 📋 Resource Index

1. **[awesome-copilot-recommendations.md](./awesome-copilot-recommendations.md)** - Main reference with quick links
2. **[agents/awesome-copilot-agents.md](./agents/awesome-copilot-agents.md)** - Expert agent reference
3. **[prompts/awesome-copilot-generators.md](./prompts/awesome-copilot-generators.md)** - Generators and prompts
4. **[instructions/awesome-copilot-instructions.md](./instructions/awesome-copilot-instructions.md)** - Key instruction patterns

### 📚 Full Documentation

- **[docs/AWESOME-COPILOT-RESOURCES.md](../docs/AWESOME-COPILOT-RESOURCES.md)** - Comprehensive resource list
- **[Copilot-Processing.md](../Copilot-Processing.md)** - Task tracking (root level)

---

## What's Installed

```
.github/
├── awesome-copilot-recommendations.md    # Main index
├── awesome-copilot-INDEX.md              # This file
├── agents/
│   └── AWESOME-COPILOT-AGENTS.md        # Agent reference
├── prompts/
│   └── AWESOME-COPILOT-GENERATORS.md    # Generators and prompts
└── instructions/
    └── AWESOME-COPILOT-INSTRUCTIONS.md  # Instruction patterns
```

---

## Getting Started

### 1. Use Expert Agents

Open Copilot Chat and type:

```
@python-mcp-expert Help me implement X
@task-planner Break down feature Y
@se-security-reviewer Review this code
```

See [agents/AWESOME-COPILOT-AGENTS.md](./agents/AWESOME-COPILOT-AGENTS.md) for all available agents.

### 2. Run Generators

Create documentation and code scaffolds:

```
/run python-mcp-server-generator
/run technology-stack-blueprint-generator
/run multi-stage-dockerfile
```

See [prompts/AWESOME-COPILOT-GENERATORS.md](./prompts/AWESOME-COPILOT-GENERATORS.md) for details.

### 3. Apply Instruction Standards

Reference when writing code:

- **Python code:** Apply `python.instructions.md` patterns
- **MCP servers:** Apply `python-mcp-server.instructions.md` patterns
- **Docker:** Apply `containerization-docker-best-practices.instructions.md` patterns

See [instructions/AWESOME-COPILOT-INSTRUCTIONS.md](./instructions/AWESOME-COPILOT-INSTRUCTIONS.md).

---

## Workflow Examples

### Planning a New Feature

1. Break down with agent:

   ```
   @task-planner Break down the Qdrant L2 cache feature
   ```

2. Create implementation plan:

   ```
   @implementation-plan Build a roadmap for Phase 2.1
   ```

3. Review architecture:

   ```
   @se-system-architecture-reviewer Assess cache design
   ```

### Implementing a New MCP Server

1. Generate scaffold:

   ```
   /run python-mcp-server-generator
   ```

2. Get expert guidance:

   ```
   @python-mcp-expert Optimize the tool implementations
   ```

3. Apply security review:

   ```
   @se-security-reviewer Review for vulnerabilities
   ```

### Improving Documentation

1. Generate architecture doc:

   ```
   /run architecture-blueprint-generator
   ```

2. Analyze workflows:

   ```
   /run project-workflow-analysis-blueprint-generator
   ```

3. Update guidelines:

   ```
   /run copilot-instructions-blueprint-generator
   ```

---

## Integration Points

### Code Review Checklist

- [ ] Code follows `python.instructions.md` standards
- [ ] MCP servers follow `python-mcp-server.instructions.md` patterns
- [ ] Docker changes follow containerization best practices
- [ ] Security-sensitive code reviewed by `@se-security-reviewer`
- [ ] Architecture changes reviewed by `@se-system-architecture-reviewer`

### Development Workflow

1. **Planning Phase:** Use `@task-planner` and `@implementation-plan`
2. **Implementation Phase:** Use `@python-mcp-expert` and apply instruction standards
3. **Testing Phase:** Use `@tdd-red`, `@tdd-green`, `@tdd-refactor`
4. **Review Phase:** Use `@se-security-reviewer` and architecture reviewers
5. **Documentation Phase:** Use generators to update docs

---

## Recommended Collections for AgentHub

### Core Development

- **Python MCP Server Development** - Build MCP servers with FastMCP
- **Containerization & Docker** - Production-ready Docker practices
- **Testing & Test Automation** - TDD patterns and automation
- **Security & Code Quality** - OWASP and best practices

### Project Management

- **Project Planning & Management** - Feature decomposition and roadmaps
- **Architecture & System Design** - Structural guidance
- **Code Review Patterns** - Peer review best practices

---

## Quick Reference

| Need                  | Resource                                  | Command   |
| --------------------- | ----------------------------------------- | --------- |
| Plan feature          | `@task-planner`                           | Chat      |
| Implement MCP tool    | `@python-mcp-expert`                      | Chat      |
| Review architecture   | `@se-system-architecture-reviewer`        | Chat      |
| Review security       | `@se-security-reviewer`                   | Chat      |
| Generate server       | `/run python-mcp-server-generator`        | Generator |
| Document architecture | `/run architecture-blueprint-generator`   | Generator |
| Optimize Docker       | `/run multi-stage-dockerfile`             | Generator |
| Test-driven dev       | `@tdd-red`, `@tdd-green`, `@tdd-refactor` | Agents    |

---

## Related Project Files

- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Project guidelines
- **[Copilot-Processing.md](../Copilot-Processing.md)** - Task tracking
- **[docs/](../docs/)** - Development documentation
- **[guides/](../guides/)** - User-facing guides
- **[README.md](../README.md)** - Project overview

---

## Support

For questions about awesome-copilot resources:

1. Check the full reference in [docs/AWESOME-COPILOT-RESOURCES.md](../docs/AWESOME-COPILOT-RESOURCES.md)
2. Review the appropriate agent/generator guide above
3. Refer to [.github/copilot-instructions.md](.github/copilot-instructions.md) for project context
4. See [Copilot-Processing.md](../Copilot-Processing.md) for past decisions

---

**Last Updated:** February 3, 2026

**Documentation Structure:**

- **Quick Reference:** This file
- **Detailed Reference:** Files in this directory
- **Full Resource List:** [docs/AWESOME-COPILOT-RESOURCES.md](../docs/AWESOME-COPILOT-RESOURCES.md)
- **Project Guidelines:** [.github/copilot-instructions.md](.github/copilot-instructions.md)
