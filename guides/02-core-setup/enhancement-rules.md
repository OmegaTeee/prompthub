# Prompt Enhancement Rules

> **What you'll learn:** How to configure per-client model selection, custom system prompts, and enhancement rules for optimal AI responses

---

## Overview

### What This Guide Covers
- What is prompt enhancement and why it matters
- Per-client model selection (DeepSeek-R1, Qwen3-Coder, llama3.2)
- Custom system prompts for different use cases
- Enhancement rules configuration
- When to disable enhancement

### Prerequisites
- ✅ AgentHub running with Ollama configured
- ✅ At least one model installed (`ollama list`)
- ✅ Basic understanding of how clients connect to AgentHub

### Estimated Time
- Reading: 15 minutes
- Configuration: 10 minutes

---

## What is Prompt Enhancement?

### The Problem

Different AI clients have different strengths:
- **Claude Desktop**: Best for research, writing, analysis
- **VS Code**: Best for code generation, debugging
- **Raycast**: Best for quick commands, CLI helpers

But they all send generic prompts like "Explain React hooks" or "Create a button component".

### The Solution: Enhancement

AgentHub **automatically improves** prompts before sending to AI using local Ollama models:

```
User → "Explain React hooks"

AgentHub Enhancement:
↓
"You are helping with content creation. Provide a comprehensive explanation
of React hooks with practical examples, use cases, and best practices.
Format response in clear markdown with code examples."

↓ Send to Claude Desktop
```

**Result:** Better, more targeted responses without user having to write detailed prompts.

---

## How Enhancement Works

### Architecture

```
Client Request
    ↓
AgentHub receives request with X-Client-Name header
    ↓
Enhancement Rules lookup (enhancement-rules.json)
    ↓
Ollama enhances prompt using client-specific model & system prompt
    ↓
Enhanced prompt sent to MCP server / AI service
    ↓
Response returned to client
```

### Header-Based Routing

AgentHub uses the `X-Client-Name` header to select the right model:

```bash
# Claude Desktop
X-Client-Name: claude-desktop  →  Uses DeepSeek-R1

# VS Code
X-Client-Name: vscode  →  Uses Qwen3-Coder

# Raycast
X-Client-Name: raycast  →  Uses llama3.2
```

---

## Model Selection by Client

### Why Different Models?

Each model is optimized for specific tasks:

| Model | Best For | Clients | Strengths |
|-------|----------|---------|-----------|
| **DeepSeek-R1** | Research, writing, analysis | Claude Desktop | Long-form content, citations, structured thinking |
| **Qwen3-Coder** | Code generation, debugging | VS Code | Code examples, technical accuracy, pragmatic solutions |
| **llama3.2** | Quick commands, CLI helpers | Raycast | Fast responses, concise output, action-oriented |

### Example Scenarios

#### Claude Desktop + DeepSeek-R1

**User prompt:** "Explain async/await"

**Enhanced prompt:**
```
You are assisting with content creation and research. Provide a comprehensive
explanation of async/await in JavaScript with:
- Clear definition and purpose
- Practical code examples
- Common use cases
- Best practices and pitfalls
- Comparison to promises

Format response in markdown with proper code blocks and headings.
```

**Result:** Detailed explanation with examples, 500-800 words

---

#### VS Code + Qwen3-Coder

**User prompt:** "Create a React button component"

**Enhanced prompt:**
```
You are a senior software engineer helping with code development. Generate
production-ready code for a React button component with:
- TypeScript types
- Props interface
- Click handler
- Style customization
- Accessibility attributes

Provide complete, working code with comments explaining key decisions.
```

**Result:** Complete TypeScript component with types and comments

---

#### Raycast + llama3.2

**User prompt:** "git command to undo last commit"

**Enhanced prompt:**
```
Provide the exact CLI command to undo the last git commit. Format as:
```bash
[command here]
```
Under 150 words. Include one-line explanation.
```

**Result:**
````bash
git reset --soft HEAD~1
````
Undoes commit but keeps changes staged. Use `--hard` to discard changes.

---

## Enhancement Rules Configuration

### Default Configuration

Location: `~/.local/share/agenthub/configs/enhancement-rules.json`

```json
{
  "default": {
    "enabled": true,
    "model": "llama3.2",
    "system_prompt": "You are a helpful assistant. Provide clear, concise responses."
  },
  "clients": {
    "claude-desktop": {
      "model": "deepseek-r1:latest",
      "system_prompt": "You are assisting with content creation and research. Provide comprehensive, well-structured responses with examples and citations where appropriate. Format in clear markdown.",
      "max_tokens": 2048
    },
    "vscode": {
      "model": "qwen3-coder:latest",
      "system_prompt": "You are a senior software engineer. Generate production-ready code with types, comments, and error handling. Explain key decisions. Prioritize TypeScript when applicable.",
      "max_tokens": 1024
    },
    "raycast": {
      "model": "llama3.2:latest",
      "system_prompt": "Action-oriented. CLI commands only. Under 200 words. Use bullet points. Wrap commands in ```bash blocks.",
      "max_tokens": 512
    }
  }
}
```

---

### Configuration Fields

#### Per-Client Settings

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `model` | string | Ollama model name | `"deepseek-r1:latest"` |
| `system_prompt` | string | Instructions for enhancement | `"You are a..."` |
| `max_tokens` | number | Max output length | `2048` |
| `temperature` | number | Creativity (0-1) | `0.7` |
| `enabled` | boolean | Enable/disable enhancement | `true` |

---

## Customizing Enhancement Rules

### Example 1: Add New Client

**Scenario:** You're using Obsidian and want custom enhancement.

**Add to `enhancement-rules.json`:**
```json
{
  "clients": {
    "obsidian": {
      "model": "deepseek-r1:latest",
      "system_prompt": "You are helping with note-taking and knowledge management. Provide concise summaries with bullet points. Use markdown formatting. Link to related concepts when relevant.",
      "max_tokens": 1024
    }
  }
}
```

**Update Obsidian config** to use `X-Client-Name: obsidian` header.

---

### Example 2: Customize for Team

**Scenario:** Your team prefers different code style than default.

**Update VS Code client:**
```json
{
  "clients": {
    "vscode": {
      "model": "qwen3-coder:latest",
      "system_prompt": "You are a senior software engineer at [Company]. Follow our code style:\n- Always use functional components\n- Prefer React hooks over class components\n- Use async/await over promises\n- Add JSDoc comments for all functions\n- Prefer named exports\n\nGenerate production-ready code following these conventions.",
      "max_tokens": 1024
    }
  }
}
```

---

### Example 3: Multi-Language Support

**Scenario:** You want code examples in multiple languages.

```json
{
  "clients": {
    "vscode-python": {
      "model": "qwen3-coder:latest",
      "system_prompt": "Python expert. Use type hints, docstrings, and PEP 8 style. Prefer f-strings, dataclasses, and async/await."
    },
    "vscode-rust": {
      "model": "qwen3-coder:latest",
      "system_prompt": "Rust expert. Use idiomatic Rust patterns. Explain ownership and borrowing. Include error handling with Result/Option."
    }
  }
}
```

**Update VS Code settings.json:**
```json
{
  "claude.mcp.servers": {
    "agenthub-python": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Client-Name": "vscode-python"
      }
    },
    "agenthub-rust": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Client-Name": "vscode-rust"
      }
    }
  }
}
```

---

## System Prompt Best Practices

### Structure

**Effective system prompts have:**
1. **Role definition:** "You are a [role]..."
2. **Task specification:** "Generate code with..."
3. **Format requirements:** "Use markdown / code blocks"
4. **Constraints:** "Under 200 words" or "TypeScript only"

---

### Good Examples

#### Research Assistant (Claude Desktop)
```
You are a research assistant helping with content creation. Provide:
- Comprehensive explanations with real-world examples
- Citations or references when making claims
- Structured markdown with clear headings
- Code examples in fenced blocks
- Bullet points for key takeaways
```

#### Code Generator (VS Code)
```
You are a senior software engineer. Generate production-ready code with:
- TypeScript types and interfaces
- Comprehensive error handling
- Inline comments explaining complex logic
- Unit test examples
- Adherence to SOLID principles
```

#### Quick Helper (Raycast)
```
Action-oriented CLI expert. Format:
```bash
[exact command]
```
One-line explanation. Under 150 words total. No verbose descriptions.
```

---

### Anti-Patterns

❌ **Too vague:**
```
"You are helpful."
```

❌ **Too restrictive:**
```
"Only provide code. No explanations. No markdown. No examples."
```
Result: Missing context, hard to understand

❌ **Contradictory:**
```
"Be comprehensive and detailed, but under 50 words."
```

---

## When to Use Enhancement

### ✅ Enable Enhancement For

- **Content creation** (Claude Desktop) - Better research, citations, structure
- **Code generation** (VS Code) - Better examples, types, error handling
- **Quick commands** (Raycast) - Concise, actionable output
- **Team workflows** - Enforce code style, conventions
- **Specialized domains** - Add domain-specific knowledge

---

### ❌ Disable Enhancement For

- **Interactive coding** - User wants to write code themselves
- **Debugging sessions** - Need exact user intent, no rephrasing
- **Performance-critical** - Skip enhancement overhead (~500ms)
- **Testing enhancement** - Want to test without enhancement layer

---

## Disabling Enhancement

### Per-Request (Header)

```bash
curl -X POST http://localhost:9090/mcp/context7/query \
  -H "X-Enhance: false" \
  -d '{"query": "React hooks"}'
```

---

### Per-Client (Config)

**In `enhancement-rules.json`:**
```json
{
  "clients": {
    "vscode-debug": {
      "enabled": false
    }
  }
}
```

**In VS Code `settings.json`:**
```json
{
  "claude.mcp.servers": {
    "agenthub-no-enhance": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Client-Name": "vscode-debug",
        "X-Enhance": "false"
      }
    }
  }
}
```

---

### Globally (Environment)

**In `.env`:**
```bash
# Disable enhancement completely
ENHANCEMENT_ENABLED=false
```

**Restart AgentHub:**
```bash
launchctl restart com.agenthub.router
```

---

## Testing Enhancement

### View Enhanced Prompts

**Check activity log:**
```bash
curl http://localhost:9090/dashboard/activity-partial | jq '.[] | {client, original_prompt, enhanced_prompt}'
```

**Output:**
```json
{
  "client": "vscode",
  "original_prompt": "Create a button",
  "enhanced_prompt": "You are a senior software engineer. Generate production-ready code for a React button component with TypeScript types..."
}
```

---

### A/B Testing

**Test with and without enhancement:**
```bash
# With enhancement
curl -X POST http://localhost:9090/mcp/context7/query \
  -H "X-Client-Name: vscode" \
  -d '{"query": "Explain closures"}'

# Without enhancement
curl -X POST http://localhost:9090/mcp/context7/query \
  -H "X-Client-Name: vscode" \
  -H "X-Enhance: false" \
  -d '{"query": "Explain closures"}'
```

Compare response quality, length, and accuracy.

---

## Performance Considerations

### Enhancement Overhead

**Typical enhancement time:**
- llama3.2: ~300ms
- qwen3-coder: ~500ms
- deepseek-r1: ~800ms

**Factors:**
- Model size (larger = slower)
- Prompt length
- System load

---

### Caching

AgentHub caches enhanced prompts (LRU cache):
```bash
# Cache configuration in .env
CACHE_MAX_SIZE=100
CACHE_SIMILARITY_THRESHOLD=0.85
```

**Effect:** Repeated prompts use cached enhancement (< 10ms)

---

## Troubleshooting

### Enhancement Not Working

**Symptom:** Responses don't seem enhanced

**Check:**
1. Verify model is installed:
   ```bash
   ollama list | grep deepseek-r1
   ```

2. Check enhancement rules:
   ```bash
   cat ~/.local/share/agenthub/configs/enhancement-rules.json | jq '.clients."claude-desktop"'
   ```

3. Verify X-Client-Name header:
   ```bash
   curl http://localhost:9090/dashboard/activity-partial | grep "claude-desktop"
   ```

---

### Enhancement Too Slow

**Symptom:** Responses take > 2 seconds

**Solutions:**
1. Use faster model:
   ```json
   {
     "model": "llama3.2:latest"  // Instead of deepseek-r1
   }
   ```

2. Reduce max_tokens:
   ```json
   {
     "max_tokens": 512  // Instead of 2048
   }
   ```

3. Disable for performance-critical clients

---

### Wrong Model Used

**Symptom:** VS Code using DeepSeek-R1 instead of Qwen3-Coder

**Check header:**
```bash
# In VS Code settings.json
{
  "claude.mcp.servers": {
    "agenthub": {
      "headers": {
        "X-Client-Name": "vscode"  // Must match enhancement-rules.json
      }
    }
  }
}
```

---

## Key Takeaways

- ✅ Enhancement improves prompts using local Ollama models
- ✅ Per-client model selection: DeepSeek-R1, Qwen3-Coder, llama3.2
- ✅ Custom system prompts for specialized use cases
- ✅ Configure via `enhancement-rules.json`
- ✅ Disable per-request, per-client, or globally
- ✅ Caching reduces overhead for repeated prompts
- ✅ Test with activity log and A/B comparisons

---

## Next Steps

**Related Guides:**
- [Circuit Breaker](circuit-breaker.md) - Handle enhancement failures gracefully
- [Audit Logging](audit-logging.md) - Track enhancement usage
- [Claude Desktop Integration](../03-integrations/claude-desktop.md) - Configure DeepSeek-R1
- [VS Code Integration](../03-integrations/vscode.md) - Configure Qwen3-Coder
- [Raycast Integration](../03-integrations/raycast.md) - Configure llama3.2

**Advanced Topics:**
- Custom model fine-tuning
- Multi-model ensemble
- Prompt engineering best practices

---

**Last Updated:** 2026-02-06
**Audience:** All users
**Time:** 15-20 minutes
**Difficulty:** Intermediate
