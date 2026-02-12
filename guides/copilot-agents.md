# How to Use

### Project Instructions

The copilot-instructions.md file automatically provides context to Copilot when working in this project. It includes:

- Architecture overview
- Code style guidelines
- API endpoints reference
- Common patterns to follow/avoid

### Custom Agents (in Copilot Chat)

| Agent    | Invoke With | Purpose                                                  |
| -------- | ----------- | -------------------------------------------------------- |
| AgentHub | @agenthub   | General development help, architecture questions         |
| Builder  | @builder    | Module-by-module implementation following BUILD-TASKS.md |
| Reviewer | @reviewer   | Code review with project-specific checklist              |

> ★ **Insight**
>
> - **copilot-instructions.md** is automatically loaded by Copilot for all suggestions in this workspace
> - **Custom agents** are invoked manually with @agent-name in Copilot Chat
> - The **@builder** agent is particularly useful - it knows the exact module order and templates from BUILD-TASKS.md

### Example Usage

In Copilot Chat:

```sh
@agenthub How should I implement the circuit breaker?
```

```sh
@builder What's the next module to implement?
```

```sh
@reviewer Review this cache implementation for issues
```
