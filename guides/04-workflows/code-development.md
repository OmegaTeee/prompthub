# Code Development Workflow with VS Code

**Master the VS Code + AgentHub + Qwen3-Coder workflow for context-aware software development**

> **What you'll learn:** How to leverage AgentHub's Qwen3-Coder enhancement for code generation, refactoring, debugging, and test-driven development in VS Code.

---

## Overview

### What This Guide Covers
- Setting up VS Code with Qwen3-Coder enhancement
- Context-aware code generation patterns
- Multi-file refactoring workflows
- Debugging with enhanced AI assistance
- Test-driven development (TDD) with AI
- Best practices for code quality

### Prerequisites
- ✅ VS Code installed with Cline, Claude Code, or Continue extension
- ✅ AgentHub running ([Quick check](../../_shared/health-checks.md))
- ✅ Qwen3-Coder model downloaded: `ollama pull qwen2.5-coder:7b`
- ✅ Enhancement enabled in VS Code config

### Estimated Time
- Initial setup: 10 minutes
- Workflow mastery: 2-3 coding sessions

---

## Concepts

### Why Qwen3-Coder?
Qwen3-Coder is specifically trained for programming tasks and excels at:
- **Code-first responses** - Minimal explanation, maximum code
- **Multi-language support** - Python, JavaScript, TypeScript, Go, Rust, etc.
- **Context preservation** - Understands file structure and dependencies
- **Refactoring patterns** - Suggests clean, idiomatic improvements

### How Enhancement Works
When you make a request in VS Code:
1. **Your prompt** → Sent to AgentHub with `X-Enhance: true`
2. **Qwen3-Coder** → Analyzes code context and improves prompt clarity
3. **Enhanced prompt** → Forwarded to MCP servers (filesystem, etc.)
4. **Better results** → More accurate, contextual code responses

**Key benefit:** The AI understands your codebase structure, not just individual files.

---

## Step-by-Step: Initial Setup

### 1. Verify Enhancement is Active

**Check VS Code settings:**

```json
// ~/.vscode/settings.json or .vscode/settings.json (project-specific)
{
  "cline.mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Enhance": "true",
        "X-Client-Name": "vscode"
      }
    }
  }
}
```

**Test enhancement:**
1. Open VS Code
2. Open Cline/Claude Code sidebar
3. Ask: "What enhancement model am I using?"
4. Should respond: "You're using Qwen3-Coder for code-optimized responses"

---

### 2. Configure Enhancement Rules

Edit `~/.local/share/agenthub/configs/enhancement-rules.json`:

```json
{
  "vscode": {
    "model": "qwen2.5-coder:7b",
    "system_prompt": "You are a senior software engineer. Provide concise, production-ready code with minimal explanation. Focus on:\n- Clean architecture\n- Type safety\n- Error handling\n- Performance\n- Security best practices\n\nAlways include comments for complex logic.",
    "enabled": true,
    "temperature": 0.2,
    "max_tokens": 2048
  }
}
```

**Restart AgentHub:**

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

### 3. Verify MCP Servers

**Essential servers for code development:**

```bash
curl http://localhost:9090/servers
```

**Should show:**
- ✅ `filesystem` - Read/write code files
- ✅ `brave-search` - Look up documentation (optional)
- ✅ `fetch` - Fetch external examples (optional)

**If missing, add to `configs/mcp-servers.json`** (see [Core Setup](../../02-core-setup/README.md))

---

## Understanding the Workflow

### The Development Loop

```
1. Plan → 2. Generate → 3. Review → 4. Refactor → 5. Test → 6. Deploy
   ↑                                                              ↓
   └──────────────────────← Iterate ←──────────────────────────┘
```

**Where AI helps most:**
- **Plan** - Architecture suggestions, breaking down tasks
- **Generate** - Boilerplate, utilities, test cases
- **Refactor** - Clean up, optimize, modernize
- **Test** - Generate test suites, edge cases, mocks

**Where you lead:**
- **Review** - Code correctness, business logic
- **Deploy** - Production readiness, security review

---

## Common Use Cases

### Use Case 1: Context-Aware Code Generation

**Scenario:** You need a new feature that follows existing patterns.

**Workflow:**

**Step 1:** Show AI the existing pattern

```
Prompt: "Review the UserService class in src/services/user.ts"
```

**Step 2:** Request similar implementation

```
Prompt: "Create a ProductService class following the same pattern as UserService. Include:
- CRUD operations
- Input validation
- Error handling with custom errors
- TypeScript types"
```

**Step 3:** Review generated code
- Check type safety
- Verify error handling matches project patterns
- Ensure naming conventions are consistent

**Step 4:** Integrate and test

```
Prompt: "Generate unit tests for ProductService using Jest, matching the test patterns in __tests__/services/user.test.ts"
```

**Why this works:**
- AI sees existing patterns via filesystem MCP server
- Qwen3-Coder understands code structure conventions
- Enhanced context produces consistent, idiomatic code

---

### Use Case 2: Multi-File Refactoring

**Scenario:** Rename a function used across multiple files.

**Workflow:**

**Step 1:** Identify all usages

```
Prompt: "Find all files that use the function `calculateDiscount` in src/"
```

**Step 2:** Plan the refactor

```
Prompt: "I want to rename calculateDiscount to computePriceDiscount. Show me all files that need changes and propose the updates."
```

**Step 3:** Apply changes incrementally

```
Prompt: "Update src/services/pricing.ts to use computePriceDiscount"
Prompt: "Update src/utils/cart.ts to use computePriceDiscount"
Prompt: "Update __tests__/ files with the new name"
```

**Step 4:** Verify no regressions

```
Prompt: "Search for any remaining references to 'calculateDiscount' in src/"
```

**Pro tip:** Use AI to generate a refactoring checklist first:

```
Prompt: "Create a checklist of all files and test cases I need to update for this rename"
```

---

### Use Case 3: Debugging with Enhanced Context

**Scenario:** You have a bug but can't reproduce it consistently.

**Workflow:**

**Step 1:** Share error context

```
Prompt: "I'm getting 'TypeError: Cannot read property 'id' of undefined' in src/components/UserProfile.tsx. Show me the relevant code section."
```

**Step 2:** Ask for root cause analysis

```
Prompt: "Analyze the code flow leading to this error. What conditions would cause user.id to be undefined?"
```

**Step 3:** Request defensive fixes

```
Prompt: "Add proper null checks and error handling to prevent this TypeError. Use TypeScript optional chaining."
```

**Step 4:** Add logging for future debugging

```
Prompt: "Add debug logging before the error line to trace the user object state"
```

**Enhanced debugging features:**
- AI reads multiple related files to understand data flow
- Suggests defensive programming patterns
- Identifies edge cases you might have missed

---

### Use Case 4: Test-Driven Development (TDD)

**Scenario:** Write tests before implementation.

**Workflow:**

**Step 1:** Define test cases

```
Prompt: "I need to implement a validateEmail function. Generate comprehensive Jest test cases covering:
- Valid email formats
- Invalid formats (missing @, invalid domain, etc.)
- Edge cases (empty string, null, undefined)
- International characters
- Length limits"
```

**Step 2:** Review and adjust tests
- Ensure tests cover business requirements
- Add domain-specific edge cases
- Verify test descriptions are clear

**Step 3:** Implement to pass tests

```
Prompt: "Implement the validateEmail function to pass all these tests. Use a regex that follows RFC 5322 standards."
```

**Step 4:** Refine implementation

```
Prompt: "Optimize the validateEmail function for performance. Can we avoid regex for basic checks?"
```

**TDD benefits with AI:**
- Comprehensive test coverage from the start
- AI generates edge cases you might miss
- Implementation follows test specification exactly

---

### Use Case 5: Code Review Assistance

**Scenario:** Review a pull request or your own code before committing.

**Workflow:**

**Step 1:** Request code review

```
Prompt: "Review src/api/auth.ts for:
- Security vulnerabilities
- Performance issues
- Code smells
- Missing error handling
- TypeScript best practices"
```

**Step 2:** Address specific concerns

```
Prompt: "The review mentions a SQL injection risk in line 45. Show me the vulnerable code and suggest a parameterized query."
```

**Step 3:** Improve code quality

```
Prompt: "Refactor the validatePassword function to be more maintainable. Extract magic numbers into constants."
```

**Step 4:** Document changes

```
Prompt: "Generate JSDoc comments for all exported functions in this file"
```

---

### Use Case 6: Learning New Patterns

**Scenario:** Adopt a new pattern or library in your codebase.

**Workflow:**

**Step 1:** Understand the pattern

```
Prompt: "Explain the Repository pattern and show an example implementation in TypeScript"
```

**Step 2:** See it in context

```
Prompt: "Convert src/services/user.ts to use the Repository pattern. Keep the existing API but restructure the internals."
```

**Step 3:** Apply to similar files

```
Prompt: "Now convert src/services/product.ts to use the same Repository pattern"
```

**Step 4:** Create migration guide

```
Prompt: "Document how we're using the Repository pattern in this codebase. Include when to use it and when not to."
```

**Learning accelerators:**
- See patterns applied to your actual code
- Ask "why" questions about design decisions
- Generate migration guides for team adoption

---

## Advanced Techniques

### Technique 1: Chain-of-Thought Code Generation

Instead of asking for complete solutions immediately, break down requests:

**Basic request:**

```
❌ "Create a user authentication system"
```

**Chain-of-thought approach:**

```
✅ "First, what are the components of a user authentication system?"
✅ "Design the database schema for user accounts with secure password storage"
✅ "Implement the User model with password hashing"
✅ "Create the AuthService with login/logout methods"
✅ "Add JWT token generation and validation"
✅ "Write middleware to protect routes"
✅ "Generate integration tests for the auth flow"
```

**Benefits:**
- Better code quality (AI thinks through design)
- More control over architecture decisions
- Easier to review incremental changes

---

### Technique 2: Contextual Documentation Generation

Leverage AI's understanding of your codebase structure:

```
Prompt: "Generate API documentation for all exported functions in src/api/, following the JSDoc format used in src/services/user.ts"
```

**Key phrase:** "following the JSDoc format used in..." ensures consistency.

---

### Technique 3: Performance Optimization

Use AI to identify bottlenecks:

```
Prompt: "Analyze src/utils/data-processor.ts for performance issues. Consider:
- Time complexity of algorithms
- Unnecessary iterations
- Memory usage patterns
- Database query efficiency
- Suggest optimizations with code examples"
```

---

### Technique 4: Security Hardening

Request security-focused code reviews:

```
Prompt: "Security audit src/api/payment.ts for:
- Input validation gaps
- SQL injection vulnerabilities
- XSS attack vectors
- Authentication bypass risks
- Sensitive data exposure
- Rate limiting needs
Provide specific fixes for each issue found."
```

---

## Best Practices

### 1. Prompt Engineering for Code

**Be specific about:**
- Language/framework versions (TypeScript 5.x, React 18, etc.)
- Code style preferences (functional vs. OOP, async/await vs. promises)
- Constraints (performance, bundle size, compatibility)

**Example:**

```
✅ "Create a React 18 functional component using TypeScript. Use hooks (useState, useEffect). Keep it under 100 lines. Follow Airbnb style guide."

❌ "Make a React component"
```

---

### 2. Iterative Refinement

Don't expect perfect code on the first try:

```
1st prompt: "Create a basic user registration form"
2nd prompt: "Add email validation using regex"
3rd prompt: "Add password strength indicator"
4th prompt: "Extract validation logic into a custom hook"
5th prompt: "Add error messages and loading states"
```

---

### 3. Review Generated Code Critically

**Always verify:**
- ✅ Type safety (no `any` types without reason)
- ✅ Error handling (try/catch blocks, null checks)
- ✅ Edge cases (empty arrays, undefined values)
- ✅ Security (input validation, sanitization)
- ✅ Performance (avoid N+1 queries, unnecessary loops)

**AI is a copilot, not an autopilot.** You're still responsible for code quality.

---

### 4. Leverage Context Window Effectively

**Good context:**
- Show related files: "Consider these files: src/types.ts, src/config.ts"
- Reference existing patterns: "Match the style in src/services/base.ts"
- Provide error messages: "This is the error I'm getting..."

**Avoid:**
- Vague requests: "Fix the bug"
- Missing context: "Create a function" (function for what?)
- Too broad: "Build the entire backend"

---

### 5. Maintain Code Consistency

Create a project-specific prompt template:

```markdown
## Project Context
- Language: TypeScript 5.x
- Framework: Next.js 14 (App Router)
- State: Zustand
- Styling: Tailwind CSS
- Testing: Jest + React Testing Library

## Code Standards
- Use functional components with hooks
- Prefer arrow functions
- Use `const` over `let`
- Always include TypeScript types (no `any`)
- Follow DRY principle
- Max function length: 30 lines

## Request
[Your specific request here]
```

Save this in your project as `.ai-context.md` and reference it:

```
Prompt: "Following the standards in .ai-context.md, create a user profile component"
```

---

## Troubleshooting

### Issue: Generated code doesn't follow project patterns

**Solution:** Provide explicit examples

```
Prompt: "This code doesn't match our patterns. Here's how we structure services: [paste example]. Regenerate following this pattern."
```

---

### Issue: AI suggests outdated or deprecated APIs

**Solution:** Specify versions

```
Prompt: "Use React 18 hooks API (not class components). We're on Node.js 20 (use native fetch, not axios)."
```

---

### Issue: Code is over-engineered

**Solution:** Request simplicity

```
Prompt: "This solution is too complex. Simplify it. Use the minimum code needed. Avoid abstractions unless there are 3+ use cases."
```

---

### Issue: Type errors in generated TypeScript

**Solution:** Request type-safe code explicitly

```
Prompt: "Ensure all function parameters have explicit types. No `any` types. Return types should be inferred or explicit."
```

---

### Issue: Enhancement feels slow

**Check Ollama performance:**

```bash
time ollama run qwen2.5-coder:7b "test"
```

**If slow (>3 seconds):**
- Use smaller model: `qwen2.5-coder:1.5b`
- Disable enhancement for quick edits (set `X-Enhance: false`)
- Check system resources: `top -o cpu`

See [Enhancement Rules](../../02-core-setup/enhancement-rules.md) for performance tuning.

---

## Key Takeaways

- ✅ **Qwen3-Coder is optimized for code** - Provides concise, production-ready implementations
- ✅ **Context is king** - Show AI existing patterns for consistent code generation
- ✅ **Iterate incrementally** - Break large tasks into smaller, reviewable steps
- ✅ **TDD with AI** - Generate comprehensive tests first, implement to pass them
- ✅ **Review critically** - AI accelerates development but you ensure quality
- ✅ **Chain-of-thought** - Ask AI to think through design before generating code
- ✅ **Maintain consistency** - Reference project standards and existing patterns

**Next steps:**
- Explore [Content Creation Workflow](content-creation.md) for documentation
- See [Quick Commands](quick-commands.md) for productivity shortcuts
- Configure [Enhancement Rules](../../02-core-setup/enhancement-rules.md) for custom behavior

---

**Last Updated:** 2026-02-05
**Workflow Difficulty:** Intermediate
**Time to Master:** 2-3 coding sessions
**Prerequisites:** VS Code + AgentHub + Qwen3-Coder
