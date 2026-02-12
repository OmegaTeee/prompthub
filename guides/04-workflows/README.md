# Practical Workflows

**Real-world usage patterns and best practices for maximizing productivity with AgentHub**

Learn how to combine AgentHub's features for productive workflows across different use cases.

---

## Available Workflow Guides

### 1. [Code Development](code-development.md)
**VS Code + Qwen3-Coder workflow for software engineering**

- Context-aware code generation
- Multi-file refactoring
- Debugging with enhanced assistance
- Test-driven development (TDD)
- Code review and optimization

**Best for:** Software developers, engineers
**Time to learn:** 2-3 coding sessions
**Difficulty:** Intermediate

---

### 2. [Content Creation](content-creation.md)
**Claude Desktop + DeepSeek-R1 workflow for writing and research**

- Research synthesis from multiple sources
- Long-form content generation
- Fact-checking and citations
- Content refinement workflows
- Multi-format repurposing

**Best for:** Writers, researchers, content creators
**Time to learn:** 3-4 writing sessions
**Difficulty:** Beginner to Intermediate

---

### 3. [Quick Commands](quick-commands.md)
**Raycast + AgentHub workflow for rapid productivity**

- Lightning-fast documentation lookup
- Command-line helpers and snippets
- Quick calculations and conversions
- Contextual clipboard operations
- Custom command creation

**Best for:** Power users, developers, anyone seeking efficiency
**Time to learn:** 1-2 days of daily use
**Difficulty:** Beginner

---

### 4. [Design to Code](design-to-code.md)
**Figma → Claude Desktop workflow for implementation**

- Design token extraction
- Component generation from designs
- Design system documentation
- Figma-to-code synchronization
- Animation implementation

**Best for:** Frontend developers, designers who code
**Time to learn:** 3-5 design implementations
**Difficulty:** Intermediate

---

## Choosing the Right Workflow

| Your Goal | Recommended Workflow |
|-----------|---------------------|
| Build software features | [Code Development](code-development.md) |
| Write articles/documentation | [Content Creation](content-creation.md) |
| Quick reference/commands | [Quick Commands](quick-commands.md) |
| Implement designs | [Design to Code](design-to-code.md) |
| Research complex topics | [Content Creation](content-creation.md) |
| Refactor codebase | [Code Development](code-development.md) |
| Generate design system | [Design to Code](design-to-code.md) |

---

## Combining Workflows

Many tasks benefit from multiple workflows:

**Example: Building a new feature**
1. **Design to Code** - Implement UI from Figma
2. **Code Development** - Add business logic and tests
3. **Content Creation** - Write documentation
4. **Quick Commands** - Deploy and verify

**Example: Technical blog post**
1. **Quick Commands** - Research API documentation
2. **Code Development** - Create code examples
3. **Content Creation** - Write and refine article

**Example: Design system**
1. **Design to Code** - Extract tokens and components
2. **Code Development** - Build Storybook stories
3. **Content Creation** - Document usage guidelines

---

## Prerequisites

Before diving into workflows, ensure you've completed:

### 1. ✅ Core Setup
- AgentHub installed and running
- LaunchAgent configured for auto-start
- Credentials stored in Keychain

**See:** [02-core-setup](../02-core-setup/)

---

### 2. ✅ Client Integration
- At least one client connected (Claude Desktop, VS Code, or Raycast)
- Enhancement enabled
- MCP servers responding

**See:** [03-integrations](../03-integrations/)

---

### 3. ✅ Enhancement Models
Download models based on workflows you'll use:

```bash
# For Code Development (VS Code)
ollama pull qwen2.5-coder:7b

# For Content Creation (Claude Desktop)
ollama pull deepseek-r1:7b

# For Quick Commands (Raycast)
ollama pull llama3.2

# Check models are available
ollama list
```

---

## Workflow Optimization Tips

### 1. Configure Enhancement Per Client

Edit `~/.local/share/agenthub/configs/enhancement-rules.json`:

```json
{
  "vscode": {
    "model": "qwen2.5-coder:7b",
    "temperature": 0.2,
    "system_prompt": "Concise, production-ready code"
  },
  "claude-desktop": {
    "model": "deepseek-r1:7b",
    "temperature": 0.7,
    "system_prompt": "Structured reasoning, well-researched content"
  },
  "raycast": {
    "model": "llama3.2",
    "max_tokens": 512,
    "system_prompt": "Maximum 200 words, action-oriented"
  }
}
```

**See:** [Enhancement Rules](../02-core-setup/enhancement-rules.md) (coming soon)

---

### 2. Use Keyboard Shortcuts

**macOS shortcuts:**
- Claude Desktop: Cmd+Space → "Claude"
- VS Code: Cmd+Shift+P → "Cline: Chat"
- Raycast: Cmd+Space (default)

**Customize for faster access**

---

### 3. Maintain Context Files

Create project-specific context:

**`.ai-context.md` in your project:**

```markdown
## Tech Stack
- Framework: Next.js 14
- Language: TypeScript 5.x
- Styling: Tailwind CSS

## Conventions
- Use functional components
- Prefer hooks over classes
- Max function length: 30 lines
```

**Reference in prompts:** "Following `.ai-context.md`, create..."

---

### 4. Track Common Patterns

Save frequently used prompts:

**Create `~/.agenthub-prompts/`:**

```bash
mkdir -p ~/.agenthub-prompts

# Save common prompts
echo "Generate Jest test cases for this function" > ~/.agenthub-prompts/test-gen.txt
echo "Review this code for security issues" > ~/.agenthub-prompts/security-review.txt
```

**Use with:** `cat ~/.agenthub-prompts/test-gen.txt` → paste in client

---

## Troubleshooting Workflows

### Issue: Wrong model being used

**Check active client:**

```bash
curl http://localhost:9090/dashboard
```

**Verify enhancement rules:**

```bash
cat ~/.local/share/agenthub/configs/enhancement-rules.json
```

**Restart AgentHub:**

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

### Issue: Slow responses

**Check model size:**

```bash
ollama list
```

**Use smaller/faster models:**
- `qwen2.5-coder:1.5b` (faster than 7b)
- `llama3.2:1b` (fastest)

**Disable enhancement for quick tasks:**
Set `X-Enhance: false` in client config

---

### Issue: Context not preserved

**Ensure filesystem MCP server is running:**

```bash
curl http://localhost:9090/servers
```

**Check recent files are accessible:**

```bash
curl -X POST http://localhost:9090/mcp/filesystem/list_allowed_directories \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"list_allowed_directories","params":{}}'
```

---

## Next Steps

1. **Choose your primary workflow** - Start with the one matching your daily tasks
2. **Complete the tutorial** - Follow the step-by-step guide in your chosen workflow
3. **Practice 3-5 times** - Workflows become natural with repetition
4. **Customize enhancement** - Adjust system prompts to match your needs
5. **Explore combinations** - Mix workflows for complex tasks

---

## Additional Resources

- [Common Troubleshooting](../_shared/troubleshooting-common.md) - Solutions for frequent issues
- [Health Checks](../_shared/health-checks.md) - Verify AgentHub is running correctly
- [Terminology](../_shared/terminology.md) - Standard terminology reference
- [Integration Tests](../05-testing/integration-tests.md) - Comprehensive testing guide

---

**Last Updated:** 2026-02-05
**Status:** ✅ Complete - All 4 workflow guides available
**Prerequisites:** Completed [01-getting-started](../01-getting-started/) and [02-core-setup](../02-core-setup/)
