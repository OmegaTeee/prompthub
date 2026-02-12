# Awesome-Copilot Generators & Prompts for AgentHub

Reference for using awesome-copilot generators and prompts to create documentation and code.

## Project Analysis Generators

### technology-stack-blueprint-generator

**Purpose:** Document and analyze the current architecture and technology stack.

**Output:** Comprehensive document describing:

- Technology choices and justifications
- Architecture patterns used
- Dependencies and their purposes
- Integration points
- Performance characteristics

**Usage:**

```
/run technology-stack-blueprint-generator
```

**When to Use:**

- During architecture reviews
- When onboarding new team members
- Before major refactoring decisions
- For documentation updates

---

### architecture-blueprint-generator

**Purpose:** Create comprehensive architecture documentation.

**Output:** Detailed architecture blueprint including:

- System components and their relationships
- Data flows
- Integration patterns
- Deployment architecture
- Scaling considerations

**Usage:**

```
/run architecture-blueprint-generator
```

**When to Use:**

- Before implementing new features
- When making architectural changes
- For design reviews with stakeholders
- To keep docs current

---

### project-workflow-analysis-blueprint-generator

**Purpose:** Document end-to-end workflows and processes.

**Output:** Workflow diagrams and descriptions for:

- Request routing flows
- Cache hit/miss scenarios
- Enhancement pipeline
- Error handling paths
- User integration workflows

**Usage:**

```
/run project-workflow-analysis-blueprint-generator
```

**When to Use:**

- Understanding complex flows
- Training new developers
- Identifying bottlenecks
- Planning optimizations

---

## Code Generation Generators

### python-mcp-server-generator

**Purpose:** Generate complete MCP server projects from scratch.

**Output:** A complete, working MCP server including:

- Server scaffold with FastMCP
- Tool definitions with type hints
- Error handling
- Logging setup
- Tests and documentation

**Usage:**

```
/run python-mcp-server-generator
```

**Parameters:**

- Server name
- List of tools to implement
- Authentication requirements
- Resource types needed

**When to Use:**

- Starting a new MCP server
- Creating wrapper servers for external services
- Prototyping new MCP capabilities

---

### multi-stage-dockerfile

**Purpose:** Generate optimized multi-stage Dockerfiles.

**Output:** Production-ready Dockerfile with:

- Multi-stage build optimization
- Minimal base image
- Non-root user setup
- Health checks
- Security best practices
- Documentation

**Usage:**

```
/run multi-stage-dockerfile
```

**When to Use:**

- Optimizing Docker builds
- Reviewing existing Dockerfile
- Setting up new services
- Improving security posture

---

## Documentation & Improvement Generators

### copilot-instructions-blueprint-generator

**Purpose:** Generate or improve the project's copilot-instructions.md file.

**Output:** Enhanced or created copilot-instructions including:

- Project overview
- Architecture patterns
- Code style guidelines
- Testing patterns
- Key file references
- Common tasks
- Team workflows

**Usage:**

```
/run copilot-instructions-blueprint-generator
```

**When to Use:**

- Starting a new project
- Updating project guidelines
- Improving Copilot integration
- Onboarding new team members

**Note:** For AgentHub, this is already maintained in `.github/copilot-instructions.md`.

---

### performance-optimization

**Purpose:** Identify and optimize performance issues in code.

**Output:** Analysis and recommendations including:

- Bottleneck identification
- Optimization opportunities
- Benchmarking suggestions
- Resource efficiency improvements
- Caching strategies
- Async/await optimization

**Usage:**

```
/run performance-optimization
```

**When to Use:**

- After profiling shows slowdowns
- During refactoring
- Before scaling up
- Optimizing critical paths

---

## Usage Workflow

### Step 1: Analysis Phase

Generate current state documentation:

```bash
/run technology-stack-blueprint-generator
/run architecture-blueprint-generator
/run project-workflow-analysis-blueprint-generator
```

**Output:** README updates, architecture diagrams, workflow documentation

---

### Step 2: Planning Phase

Break down the feature using agents:

```
@task-planner Break down the Qdrant L2 cache feature
```

---

### Step 3: Implementation Phase

Generate code scaffolds if needed:

```
/run python-mcp-server-generator
@python-mcp-expert Implement the cache optimization tool
```

---

### Step 4: Optimization Phase

After implementation:

```
/run performance-optimization
@se-security-reviewer Review for security issues
```

---

### Step 5: Documentation Phase

Update project docs:

```
/run multi-stage-dockerfile  (if adding Docker service)
/run copilot-instructions-blueprint-generator  (if guidelines changed)
```

---

## Best Practices

1. **Generate incrementally:** Create one section at a time, review, then integrate
2. **Review output carefully:** Generators provide templates; customize for your needs
3. **Keep docs in sync:** Update generators when architecture changes significantly
4. **Use for onboarding:** Generated docs are excellent for new team members
5. **Version your blueprints:** Store generated outputs in documentation folders

---

## Integration with AgentHub

### Current Generated Documentation

- `.github/copilot-instructions.md` - Project guidelines
- `docs/AWESOME-COPILOT-RESOURCES.md` - Resource reference
- Architecture docs in `docs/architecture/`

### Recommended Regeneration Schedule

- **Monthly:** Run performance-optimization against main branch
- **Quarterly:** Regenerate technology and architecture blueprints
- **Per Release:** Update workflow diagrams and deployment docs
- **Per Major Feature:** Update architecture blueprints

---

## Related Resources

- [awesome-copilot-recommendations.md](./awesome-copilot-recommendations.md) - Main index
- [agents/AWESOME-COPILOT-AGENTS.md](./agents/AWESOME-COPILOT-AGENTS.md) - Agent reference
- [copilot-instructions.md](./copilot-instructions.md) - Project guidelines
