# Claude Desktop Integration with AgentHub

> **Complete guide to connecting Claude Desktop to AgentHub for unified MCP access**

---

## Overview

AgentHub acts as a **centralized MCP proxy** for Claude Desktop, providing:

1. **Unified Access** - Access all 7+ MCP servers through a single connection
2. **Prompt Enhancement** - Automatically improve prompts with DeepSeek-R1 reasoning
3. **Auto-Restart** - MCP servers automatically restart if they crash
4. **Caching** - Faster responses through intelligent caching
5. **Audit Logging** - Track all MCP requests for debugging

### Architecture

```
┌─────────────────┐
│ Claude Desktop  │
│                 │
│  X-Client-Name: │
│ "claude-desktop"│
└────────┬────────┘
         │ JSON-RPC over stdio
         ▼
┌─────────────────────────────────┐
│      AgentHub Router            │
│     localhost:9090              │
│                                 │
│  1. Prompt Enhancement          │
│     (DeepSeek-R1:latest)        │
│  2. Circuit Breaker Check       │
│  3. Route to MCP Server         │
│  4. Cache Response              │
└────────┬────────────────────────┘
         │
         ├──────► context7 (docs)
         ├──────► desktop-commander (files)
         ├──────► sequential-thinking (reasoning)
         ├──────► memory (persistence)
         ├──────► deepseek-reasoner (local AI)
         ├──────► fetch (web)
         └──────► obsidian (notes)
```

---

## Prerequisites

Before starting, ensure:

- [ ] **AgentHub is running**: `curl http://localhost:9090/health` returns healthy
- [ ] **Claude Desktop installed**: Version 1.0+ (with MCP support)
- [ ] **Ollama running**: For prompt enhancement (optional but recommended)
- [ ] **7+ MCP servers running**: Check via `curl http://localhost:9090/servers`

---

## Example Configurations

AgentHub provides example configurations in `clients/claude/`:

- **`claude-desktop-unified.json`** - ⭐ **Recommended**: Unified MCP bridge (all 7 servers in one)
- **`claude-desktop-config.json.example`** - Alternative curl-based approach
- **`claude_desktop_config.json`** - Symlink to your actual config for quick access

**Quick copy:**
```bash
# Use the unified bridge (recommended)
cp ~/.local/share/agenthub/clients/claude/claude-desktop-unified.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

See [clients/claude/README.md](../clients/claude/README.md) for detailed configuration options.

---

## Installation Steps

### Step 1: Locate Claude Desktop Config

Claude Desktop uses a JSON configuration file for MCP servers:

```bash
# macOS location
CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Check if it exists
if [ -f "$CONFIG_PATH" ]; then
  echo "✅ Config file found"
  cat "$CONFIG_PATH"
else
  echo "⚠️  Config file not found - will be created"
fi
```

### Step 2: Backup Existing Configuration

**Always backup before making changes:**

```bash
cp "$HOME/Library/Application Support/Claude/claude_desktop_config.json" \
   "$HOME/Library/Application Support/Claude/claude_desktop_config.json.backup-$(date +%Y%m%d)"
```

### Step 3: Add AgentHub MCP Server

Claude Desktop expects MCP servers configured with `mcpServers` object. However, **AgentHub uses HTTP transport**, not stdio.

**Option A: Manual Edit** (Recommended)

Open the config file in your editor:

```bash
code "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

Add the AgentHub server:

```json
{
  "mcpServers": {
    "agenthub": {
      "command": "curl",
      "args": [
        "-s",
        "-X",
        "POST",
        "http://localhost:9090/mcp/context7/tools/call",
        "-H",
        "Content-Type: application/json",
        "-H",
        "X-Client-Name: claude-desktop",
        "-d",
        "@-"
      ]
    }
  }
}
```

**Option B: Using jq** (Automated)

```bash
CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Create config if it doesn't exist
if [ ! -f "$CONFIG_PATH" ]; then
  echo '{"mcpServers": {}}' > "$CONFIG_PATH"
fi

# Add AgentHub server
jq '.mcpServers["agenthub"] = {
  "command": "curl",
  "args": [
    "-s",
    "-X",
    "POST",
    "http://localhost:9090/mcp/context7/tools/call",
    "-H",
    "Content-Type: application/json",
    "-H",
    "X-Client-Name: claude-desktop",
    "-d",
    "@-"
  ]
}' "$CONFIG_PATH" > /tmp/claude_config.json

mv /tmp/claude_config.json "$CONFIG_PATH"
echo "✅ AgentHub added to Claude Desktop config"
```

### Step 4: Restart Claude Desktop

```bash
# Quit Claude Desktop completely
osascript -e 'quit app "Claude"'

# Wait 2 seconds
sleep 2

# Reopen
open -a "Claude"
```

---

## Verification & Testing

### Test 1: Check MCP Connection

After restarting Claude Desktop:

1. **Look for the MCP badge** at the bottom of the chat window
2. It should show: `🔌 AgentHub (7 tools)` or similar

### Test 2: List Available Tools

In Claude Desktop chat, try:

```
Show me what MCP tools are available
```

**Expected Response:**
```
Available MCP Tools via AgentHub:
- context7: Fetch documentation (React, Node.js, etc.)
- desktop-commander: File operations and terminal commands
- sequential-thinking: Step-by-step reasoning
- memory: Cross-session context storage
- deepseek-reasoner: Local reasoning without API costs
- fetch: HTTP requests and web scraping
- obsidian: Note-taking and knowledge management
```

### Test 3: Use Context7 for Documentation

```
Use context7: How do I use React useState hook?
```

**Expected Flow:**
1. Prompt sent to AgentHub
2. Enhanced by DeepSeek-R1 (adds structure/clarity)
3. Routed to context7 MCP server
4. Documentation fetched and returned
5. Response cached for future requests

**Expected Response:**
```
# React useState Hook

The useState hook is used for state management in functional components.

## Basic Syntax
`const [state, setState] = useState(initialValue);`

## Example
[Code example with explanation]

Source: context7 via AgentHub
```

### Test 4: Use Desktop Commander

```
Use desktop-commander: List files in my Downloads folder
```

**Expected Response:**
```
Files in ~/Downloads:
- document.pdf (2.3 MB)
- image.png (1.1 MB)
- archive.zip (5.7 MB)
...

Retrieved via desktop-commander MCP server
```

### Test 5: Use Sequential Thinking

```
Use sequential-thinking: Plan a marketing campaign for a new product launch
```

**Expected Response:**
```
Step-by-step plan:

Step 1: Market Research
- Identify target audience
- Analyze competitors
- ...

Step 2: Strategy Development
...

Reasoning provided by sequential-thinking MCP server
```

---

## Client-Specific Features

### Prompt Enhancement

Claude Desktop prompts are automatically enhanced with **DeepSeek-R1:latest** model (configured in `enhancement-rules.json`).

**Enhancement Settings:**
```json
{
  "claude-desktop": {
    "model": "deepseek-r1:latest",
    "system_prompt": "Provide structured responses with clear reasoning. Use Markdown."
  }
}
```

**What This Means:**
- Your prompts are rewritten for better clarity before being sent to MCP servers
- Responses are formatted with Markdown structure
- Reasoning chains are preserved and visible

**Example Enhancement:**

**Your Original Prompt:**
```
context7 react hooks
```

**Enhanced Prompt (sent to context7):**
```
Please provide comprehensive documentation about React Hooks, including:
1. Core concepts and motivation
2. useState and useEffect examples
3. Best practices and common patterns
4. References to official documentation

Format the response in structured Markdown.
```

### Response Caching

All MCP responses are cached with a 1-hour TTL. This means:
- **First request**: ~2-5 seconds (fetch from MCP server)
- **Subsequent requests**: <100ms (served from cache)

Cache is shared across all clients, so if VS Code fetches React docs, Claude Desktop gets them instantly.

### Audit Logging

Every MCP request is logged for debugging:

```bash
# View recent requests
curl http://localhost:9090/audit/activity?limit=10

# Check dashboard
open http://localhost:9090/dashboard
```

---

## Recommended Settings

### Custom Instructions for Tool Usage

To get the best experience with AgentHub's MCP tools, configure Claude Desktop's custom instructions:

**1. Open Claude Desktop Settings**
- Click Settings (gear icon) → Custom Instructions

**2. Add Tool Usage Policy**

Recommended instructions:

```
Tool Usage Policy:
- Use MCP tools automatically when they're clearly useful for the task
- Mention when you're accessing tools (e.g., "Using context7 to fetch docs...")
- Always request explicit permission before modifying system files or data
- Prefer built-in tools for file operations, documentation lookup, and web requests
```

**Why This Helps:**
- **Proactive tool use**: Claude will automatically use tools when appropriate, rather than asking permission each time
- **Transparency**: You'll know when tools are being accessed
- **Safety**: System modifications still require explicit permission
- **Better UX**: Faster workflows with fewer interruptions

**Example:**

Without custom instructions:
```
User: "What's the latest React hooks documentation?"
Claude: "Would you like me to use the context7 tool to look that up?"
User: "Yes"
Claude: [uses tool]
```

With custom instructions:
```
User: "What's the latest React hooks documentation?"
Claude: "Let me use context7 to fetch the latest React documentation...
[uses tool automatically]
Here's what I found..."
```

**Note:** These instructions persist across all conversations and apply only to your Claude Desktop instance.

---

## Troubleshooting

### Common Issues

For common AgentHub connection, health check, and MCP server issues, see:
- **[Common Troubleshooting Guide](../_shared/troubleshooting-common.md)** - Connection refused, router not responding, timeout errors
- **[Health Checks Guide](../_shared/health-checks.md)** - Verification commands and status checks

### Claude Desktop-Specific Issues

#### Issue: "MCP Server Not Found in Claude Desktop"

**Symptoms:**
- No MCP badge in Claude Desktop UI
- Error: "No MCP servers configured"

**Solutions:**

1. **Verify config file syntax:**
   ```bash
   cat "$HOME/Library/Application Support/Claude/claude_desktop_config.json" | jq .
   ```
   Should return valid JSON. If error, fix syntax.

2. **Verify curl is available:**
   ```bash
   which curl
   # Should return: /usr/bin/curl
   ```

3. **Restart Claude Desktop completely:**
   - `Cmd+Q` to quit (don't just close window)
   - Reopen Claude Desktop
   - Check for MCP badge in chat window

#### Issue: "Prompt Enhancement Not Working"

**Symptoms:**
- Responses don't seem enhanced
- Missing markdown formatting in research answers

**Solutions:**

1. **Verify DeepSeek-R1 model is installed:**
   ```bash
   ollama list | grep deepseek-r1
   # Should show: deepseek-r1:latest
   ```

2. **Pull model if missing:**
   ```bash
   ollama pull deepseek-r1:latest
   ```

3. **Check enhancement rules for claude-desktop:**
   ```bash
   cat ~/.local/share/agenthub/configs/enhancement-rules.json | jq '.clients."claude-desktop"'
   ```

4. **Verify X-Client-Name header is set:**
   ```json
   {
     "mcpServers": {
       "agenthub": {
         "args": ["-H", "X-Client-Name: claude-desktop"]
       }
     }
   }
   ```

#### Issue: "Keychain Permission Prompts"

**Symptoms:**
- Constant "Allow access to keychain?" popups
- Interrupts MCP requests

**Solutions:**

1. **Grant always-allow in Keychain Access:**
   - Open Keychain Access app
   - Search for "agenthub"
   - Double-click entry → Access Control → Always Allow

2. **Use LaunchAgent approach** (see `../02-core-setup/launchagent.md`)

---

## Advanced Configuration

### Multiple MCP Proxies

You can configure multiple AgentHub instances or combine with direct MCP servers:

```json
{
  "mcpServers": {
    "agenthub": {
      "command": "curl",
      "args": [
        "-s",
        "-X",
        "POST",
        "http://localhost:9090/mcp/context7/tools/call",
        "-H",
        "Content-Type: application/json",
        "-H",
        "X-Client-Name: claude-desktop",
        "-d",
        "@-"
      ]
    },
    "local-memory-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### Custom Client Name

Change the `CLIENT_NAME` env var to use different enhancement rules:

```json
{
  "env": {
    "CLIENT_NAME": "claude-desktop-custom"
  }
}
```

Then add custom rules in `enhancement-rules.json`:

```json
{
  "clients": {
    "claude-desktop-custom": {
      "model": "llama3.2:3b",
      "system_prompt": "Your custom prompt here"
    }
  }
}
```

### Selective Tool Access

Restrict which tools Claude Desktop can access:

```json
{
  "alwaysAllow": [
    "tools/list"
  ],
  "neverAllow": [
    "desktop-commander/execute"
  ]
}
```

---

## Performance Optimization

### Reduce Latency

1. **Use local Ollama models** (vs cloud APIs)
2. **Enable L1 cache** (already on by default)
3. **Increase cache size** in AgentHub settings:
   ```bash
   # Edit router/config/settings.py
   cache_max_size: int = 5000  # Increase from 1000
   ```

### Monitor Performance

```bash
# Check dashboard for metrics
open http://localhost:9090/dashboard

# View cache stats
curl http://localhost:9090/dashboard/stats-partial

# View activity log
curl http://localhost:9090/dashboard/activity-partial
```

---

## See Also

- [app-configs.md](app-configs.md) - Quick config reference for all clients
- [getting-started.md](getting-started.md) - AgentHub setup guide
- [launchagent-setup.md](launchagent-setup.md) - Auto-start AgentHub on login
- [keychain-setup.md](keychain-setup.md) - Credential management

---

## Quick Reference

### Config File Location
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### AgentHub Health Check
```bash
curl http://localhost:9090/health
```

### List MCP Servers
```bash
curl http://localhost:9090/servers | jq
```

### View Dashboard
```bash
open http://localhost:9090/dashboard
```

### Restart Claude Desktop
```bash
osascript -e 'quit app "Claude"' && sleep 2 && open -a "Claude"
```
