# Quick Commands Workflow with Raycast

**Master productivity shortcuts using Raycast + AgentHub for rapid information retrieval and task automation**

> **What you'll learn:** How to use Raycast with AgentHub for lightning-fast documentation lookup, quick calculations, system automation, and context-aware assistance.

---

## Overview

### What This Guide Covers
- Setting up Raycast for optimal productivity
- Quick documentation and API reference lookup
- System automation commands
- Context-aware clipboard operations
- File and project navigation shortcuts
- Custom command creation

### Prerequisites
- ✅ Raycast installed ([raycast.com](https://raycast.com))
- ✅ AgentHub running ([Quick check](../../_shared/health-checks.md))
- ✅ Enhancement configured for concise responses
- ✅ Raycast AgentHub extension configured

### Estimated Time
- Initial setup: 10 minutes
- Workflow mastery: 1-2 days of daily use

---

## Concepts

### Why Raycast for Quick Commands?

Raycast is optimized for **speed** and **context**:
- **Keyboard-first** - No mouse required, instant access (Cmd+Space)
- **Context-aware** - Knows what app you're in, what's in clipboard
- **Action-oriented** - Get answers and execute tasks in one flow
- **Minimal UI** - No distraction, just results

### How AgentHub Enhances Raycast

Without AgentHub:
- ❌ Generic responses
- ❌ No access to local files/context
- ❌ Can't search documentation offline
- ❌ Limited system integration

With AgentHub:
- ✅ Concise, action-oriented responses (<200 words default)
- ✅ Access to filesystem, brave-search, fetch
- ✅ Project-aware assistance
- ✅ Custom enhancement rules for brevity

---

## Step-by-Step: Initial Setup

### 1. Install Raycast AgentHub Extension

**In Raycast:**
1. Open Raycast (Cmd+Space)
2. Type "Extensions"
3. Search for "AgentHub" or "MCP"
4. Click "Install"

**Or configure manually:**

```bash
# Edit Raycast MCP servers config
open ~/Library/Application\ Support/com.raycast.macos/mcp_servers.json
```

Add AgentHub:

```json
{
  "agenthub": {
    "url": "http://localhost:9090",
    "headers": {
      "X-Enhance": "true",
      "X-Client-Name": "raycast"
    }
  }
}
```

---

### 2. Configure Enhancement for Conciseness

Edit `~/.local/share/agenthub/configs/enhancement-rules.json`:

```json
{
  "raycast": {
    "model": "llama3.2",
    "system_prompt": "You are a productivity assistant. Provide CONCISE, ACTION-ORIENTED responses:\n- Maximum 200 words unless complex\n- Bullet points for lists\n- Code snippets without excessive explanation\n- Quick answers, not essays\n- Skip pleasantries, get to the point\n\nUser is in a fast-paced workflow - respect their time.",
    "enabled": true,
    "temperature": 0.3,
    "max_tokens": 512
  }
}
```

**Restart AgentHub:**

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

### 3. Test Quick Command

**In Raycast:**
1. Cmd+Space
2. Type "Ask AgentHub" (or your configured trigger)
3. Enter: "What's the git command to undo last commit?"
4. Should get concise response:

   ```
   git reset HEAD~1

   This keeps changes in working directory.
   To discard changes: git reset --hard HEAD~1
   ```

---

## Understanding the Workflow

### The Quick Command Pattern

```
1. Trigger → 2. Query → 3. Result → 4. Action
   ↑                                    ↓
   └─────────────── Repeat ←───────────┘
```

**Speed is everything:**
- ⚡ Cmd+Space opens Raycast (< 50ms)
- ⚡ Type query (streaming search)
- ⚡ See results (< 2 seconds)
- ⚡ Take action (copy, open, execute)

---

## Common Use Cases

### Use Case 1: Documentation Lookup

**Scenario:** You need API syntax while coding.

**Workflow:**

**Quick reference:**

```
Raycast: "React useEffect cleanup syntax"

Response:
useEffect(() => {
  // Effect code
  return () => {
    // Cleanup code
  };
}, [dependencies]);
```

**Detailed example:**

```
Raycast: "React useEffect cleanup example with addEventListener"

Response:
useEffect(() => {
  const handler = (e) => console.log(e.key);
  window.addEventListener('keydown', handler);

  return () => {
    window.removeEventListener('keydown', handler);
  };
}, []);
```

**Follow-up questions:**

```
Raycast: "When is cleanup called?"

Response:
- Before effect runs again (if dependencies changed)
- When component unmounts
```

**Pro tip:** Use "how to" or "syntax for" for quick references, "example" for code snippets.

---

### Use Case 2: Command-Line Helpers

**Scenario:** You need a shell command but can't remember the exact syntax.

**Common queries:**

**Find files:**

```
Raycast: "find all .js files modified in last 24 hours"

Response:
find . -name "*.js" -mtime -1
```

**Text processing:**

```
Raycast: "extract column 3 from CSV"

Response:
cut -d',' -f3 file.csv
```

**System info:**

```
Raycast: "check disk usage sorted by size"

Response:
du -sh * | sort -rh
```

**Process management:**

```
Raycast: "kill process on port 3000"

Response:
lsof -ti:3000 | xargs kill -9
```

---

### Use Case 3: Quick Calculations

**Scenario:** Need math results without opening calculator.

**Simple math:**

```
Raycast: "1920 * 1080 pixels to megapixels"

Response: 2.07 megapixels (2,073,600 pixels)
```

**Unit conversions:**

```
Raycast: "Convert 256GB to bytes"

Response: 274,877,906,944 bytes (256 × 1024³)
```

**Date calculations:**

```
Raycast: "Days between Jan 1 2025 and Mar 15 2025"

Response: 73 days
```

**Financial:**

```
Raycast: "What's 15% tip on $87.50?"

Response: $13.13 tip, $100.63 total
```

---

### Use Case 4: Code Snippets

**Scenario:** You need a common code pattern quickly.

**Regex patterns:**

```
Raycast: "regex for email validation"

Response:
/^[^\s@]+@[^\s@]+\.[^\s@]+$/
```

**SQL queries:**

```
Raycast: "SQL to get top 10 by count"

Response:
SELECT column, COUNT(*) as count
FROM table
GROUP BY column
ORDER BY count DESC
LIMIT 10;
```

**API requests:**

```
Raycast: "curl POST with JSON"

Response:
curl -X POST https://api.example.com/data \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

---

### Use Case 5: Contextual Clipboard Operations

**Scenario:** Transform clipboard content on-the-fly.

**Format JSON:**

```
1. Copy unformatted JSON
2. Raycast: "format clipboard as JSON"
3. Paste formatted JSON
```

**Convert to Markdown:**

```
1. Copy HTML table
2. Raycast: "convert clipboard HTML to markdown table"
3. Paste markdown table
```

**Generate from template:**

```
1. Copy list of names
2. Raycast: "create email addresses from clipboard names using @company.com"
3. Paste email list
```

**Pro tip:** Combine with Raycast's built-in clipboard history for powerful workflows.

---

### Use Case 6: Project Context Awareness

**Scenario:** Get project-specific help based on current directory.

**Setup context:**

```
Raycast: "Remember I'm working on a Next.js 14 project using TypeScript, Tailwind, and Prisma"
```

**Then use abbreviated queries:**

```
Raycast: "create API route"

Response: (knows you're in Next.js)
// app/api/route/route.ts
export async function GET(request: Request) {
  return Response.json({ data: [] })
}
```

**Project-specific commands:**

```
Raycast: "test command"

Response: (knows your stack)
npm test -- --watch
```

---

## Advanced Techniques

### Technique 1: Command Chaining

Execute multiple related queries:

```
Raycast: "git diff HEAD~1 syntax then how to apply as patch"

Response:
1. View changes:
git diff HEAD~1

2. Create patch:
git diff HEAD~1 > changes.patch

3. Apply patch:
git apply changes.patch
```

---

### Technique 2: Keyboard Shortcuts

Create custom Raycast shortcuts for frequent commands:

**In Raycast settings:**
- "Ask AgentHub" → Cmd+Shift+A
- "Search Docs" → Cmd+Shift+D
- "Code Snippet" → Cmd+Shift+C

**Trigger instantly without typing**

---

### Technique 3: Quick Scripts

Generate and execute one-line scripts:

```
Raycast: "bash script to find all TODO comments in .js files"

Response:
grep -r "TODO" --include="*.js" .
```

**Copy → Paste in terminal → Execute**

---

### Technique 4: Fallback Chains

Use AgentHub as fallback when Raycast's built-in features don't have answer:

```
1. Try Raycast's built-in command palette
2. If not found → Ask AgentHub
3. AgentHub searches docs via brave-search MCP
4. Get answer in seconds
```

---

## Best Practices

### 1. Keep Queries Short

**Good:**

```
✅ "git rebase syntax"
✅ "React hook for window size"
✅ "convert UTC to EST"
```

**Bad:**

```
❌ "Can you please explain how to use git rebase in an interactive mode with specific commits?"
❌ "I need a React hook that will help me track the window size and update on resize events"
```

**Rule:** If query is >7 words, you're probably being too verbose.

---

### 2. Use Action Verbs

Start queries with action verbs for better results:

```
✅ "find all .env files"
✅ "convert PNG to JPEG"
✅ "format phone number"
✅ "calculate compound interest"
```

---

### 3. Leverage Context

Assume AgentHub knows your environment:

```
✅ "restart server" (knows you're working on a project)
✅ "run tests" (knows your test framework)
✅ "check logs" (knows log locations)
```

---

### 4. One Command, One Purpose

Don't combine unrelated queries:

```
❌ "git syntax and docker commands and regex"
✅ "git rebase syntax"
[separate query] "docker compose up command"
[separate query] "regex for URLs"
```

---

### 5. Use Abbreviations

Raycast supports fuzzy search, use it:

```
✅ "rn useef" → React Native useEffect
✅ "py req" → Python requests library
✅ "sql join" → SQL JOIN syntax
```

---

## Custom Commands

### Creating Project-Specific Commands

**Example: "Deploy" command**

**Setup:**
1. Raycast → Extensions → Script Commands
2. Create new script: `deploy.sh`

```bash
#!/bin/bash
# Required parameters:
# @raycast.title Deploy to Production
# @raycast.mode silent
# @raycast.packageName Project

cd ~/projects/myapp
git push origin main
echo "Deployed!"
```

**Usage:** Type "deploy" in Raycast → instant deployment

---

### Creating AgentHub Query Aliases

**Example: "Docs" command for documentation lookup**

**Setup in Raycast:**
- Alias: "docs"
- Command: Ask AgentHub with prefix "Documentation for: {query}"

**Usage:**

```
Raycast: "docs useEffect"
→ Actual query: "Documentation for: useEffect"
```

---

## Troubleshooting

### Issue: Responses are too long

**Solution:** Adjust enhancement rules

```json
{
  "raycast": {
    "max_tokens": 256,
    "system_prompt": "Maximum 100 words. Bullet points only."
  }
}
```

---

### Issue: Slow responses

**Check Ollama performance:**

```bash
time ollama run llama3.2 "test"
```

**If slow:**
- Use smaller model: `llama3.2:1b`
- Disable enhancement for simple queries
- Check system resources

---

### Issue: Wrong context

**Solution:** Be explicit

```
❌ "test command"
✅ "jest test command for React"
```

---

### Issue: Can't find recent files

**Solution:** Ensure filesystem MCP server is running

```bash
curl http://localhost:9090/servers
```

---

## Productivity Metrics

Track your efficiency gains:

**Before AgentHub + Raycast:**
- Google search: 30-60 seconds
- Find documentation: 2-5 minutes
- Recall command syntax: 1-2 minutes

**After AgentHub + Raycast:**
- Quick query: 2-5 seconds
- Get documentation: 5-10 seconds
- Get command syntax: 3-5 seconds

**Estimated time savings:** 20-30 minutes per day for heavy users.

---

## Key Takeaways

- ✅ **Speed is king** - Raycast + AgentHub optimized for < 5 second answers
- ✅ **Concise prompts** - Short queries (< 7 words) get faster responses
- ✅ **Action verbs** - "find", "convert", "calculate" work best
- ✅ **Context awareness** - AgentHub remembers your project environment
- ✅ **Keyboard shortcuts** - Cmd+Space → Query → Answer → Copy
- ✅ **Custom commands** - Automate frequent tasks with script commands
- ✅ **Clipboard integration** - Transform copied content on-the-fly

**Next steps:**
- Explore [Code Development](code-development.md) for deeper coding workflows
- See [Content Creation](content-creation.md) for writing assistance
- Configure [Enhancement Rules](../../02-core-setup/enhancement-rules.md) for custom behavior

---

**Last Updated:** 2026-02-05
**Workflow Difficulty:** Beginner
**Time to Master:** 1-2 days of daily use
**Prerequisites:** Raycast + AgentHub + llama3.2
