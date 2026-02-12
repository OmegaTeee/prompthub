# VS Code Integration with AgentHub

> **Complete guide to connecting VS Code (Claude Code / Cline) to AgentHub for code-optimized MCP access**

---

## Overview

AgentHub provides **code-optimized MCP access** for VS Code extensions like Claude Code and Cline, with:

1. **Code-First Enhancement** - Prompts enhanced with Qwen3-Coder (specialized for coding)
2. **Fast File Operations** - Desktop Commander for instant file access
3. **Documentation Lookup** - Context7 for instant API docs
4. **Reasoning Support** - Sequential thinking for complex problem-solving
5. **Workspace Integration** - Per-project MCP configuration

### Architecture

```
┌─────────────────┐
│   VS Code       │
│  Claude Code /  │
│     Cline       │
│                 │
│  X-Client-Name: │
│    "vscode"     │
└────────┬────────┘
         │ HTTP JSON-RPC
         ▼
┌─────────────────────────────────┐
│      AgentHub Router            │
│     localhost:9090              │
│                                 │
│  1. Code Enhancement            │
│     (Qwen3-Coder:latest)        │
│  2. File-Path Preservation      │
│  3. Minimal Prose Mode          │
│  4. Fast Response Cache         │
└────────┬────────────────────────┘
         │
         ├──────► context7 (API docs)
         ├──────► desktop-commander (file ops)
         ├──────► sequential-thinking (planning)
         ├──────► memory (project context)
         └──────► fetch (web resources)
```

---

## Prerequisites

- [ ] **VS Code installed**: Version 1.85+ (with extension support)
- [ ] **Claude Code or Cline extension**: Installed from marketplace
- [ ] **AgentHub running**: `curl http://localhost:9090/health` → healthy
- [ ] **Ollama with Qwen3-Coder**: `ollama pull qwen3-coder:latest`
- [ ] **Node.js 18+**: For MCP proxy client

---

## Example Configurations

AgentHub provides example configurations in `clients/vscode/`:

- **`vscode-settings.json.example`** - Minimal MCP settings for VS Code
- **`vscode.json`** - Full workspace config with tasks and shortcuts

**Quick copy:**
```bash
# Copy example to your workspace
cp ~/.local/share/agenthub/clients/vscode/vscode-settings.json.example \
   .vscode/settings.json

# Or use globally
cp ~/.local/share/agenthub/clients/vscode/vscode-settings.json.example \
   ~/.vscode/settings.json
```

See [clients/vscode/README.md](../clients/vscode/README.md) for task definitions and keyboard shortcuts.

---

## Installation Steps

### Step 1: Install Claude Code or Cline Extension

**Option A: Claude Code (Recommended for Anthropic users)**

1. Open VS Code Extensions (`Cmd+Shift+X`)
2. Search for "Claude Code"
3. Install the official extension
4. Restart VS Code

```bash
# Or via CLI
code --install-extension anthropic.claude-code
```

**Option B: Cline (Alternative)**

1. Open VS Code Extensions
2. Search for "Cline"
3. Install the extension
4. Restart VS Code

```bash
# Or via CLI
code --install-extension cline.cline
```

### Step 2: Configure MCP Settings

VS Code MCP configuration can be:
- **Global**: `~/.vscode/settings.json` (all workspaces)
- **Workspace**: `.vscode/settings.json` (current project only)

**Global Configuration (Recommended):**

```bash
# Open global settings
code ~/.vscode/settings.json
```

Add AgentHub configuration:

```json
{
  "claude.mcp.enabled": true,
  "claude.mcp.servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "transport": "http",
      "headers": {
        "X-Client-Name": "vscode"
      },
      "timeout": 30000
    }
  },
  "claude.mcp.autoConnect": true,
  "claude.mcp.cacheResponses": true
}
```

**Workspace Configuration (Per-Project):**

```bash
# Create workspace settings
mkdir -p .vscode
code .vscode/settings.json
```

Add AgentHub with project-specific settings:

```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "transport": "http",
      "headers": {
        "X-Client-Name": "vscode-project-specific"
      }
    }
  }
}
```

### Step 3: Install MCP HTTP Client (if needed)

Some VS Code extensions require a bridge for HTTP MCP servers:

```bash
# Global install
npm install -g @modelcontextprotocol/http-client

# Verify
npx @modelcontextprotocol/http-client --version
```

### Step 4: Reload VS Code

```bash
# Reload window
# In VS Code: Cmd+Shift+P → "Developer: Reload Window"

# Or restart VS Code completely
osascript -e 'quit app "Visual Studio Code"'
sleep 2
open -a "Visual Studio Code"
```

---

## Verification & Testing

### Test 1: Check MCP Connection Status

1. Open **Command Palette** (`Cmd+Shift+P`)
2. Type "Claude: Show MCP Status"
3. Should show: `✅ Connected to AgentHub (7 tools)`

**Alternative: Check via Settings UI**
1. Settings → Extensions → Claude Code → MCP Servers
2. Should list "agenthub" with green checkmark

### Test 2: List Available MCP Tools

In Claude Code chat panel, ask:

```
What MCP tools are available?
```

**Expected Response:**
```
Available MCP Tools:

📚 context7 - Fetch API documentation (React, Node.js, Python, etc.)
📁 desktop-commander - File system operations and terminal commands
🧠 sequential-thinking - Step-by-step problem solving
💾 memory - Cross-session project context
🌐 fetch - HTTP requests and web scraping
```

### Test 3: Use Context7 for Code Documentation

```
Use context7: Show me the TypeScript ReadonlyArray type documentation
```

**Expected Flow:**
1. Prompt enhanced by Qwen3-Coder → "code-first" formatting
2. Sent to context7 MCP server
3. TypeScript docs fetched
4. Returned with code examples

**Expected Response:**
```typescript
/**
 * TypeScript ReadonlyArray<T>
 * A read-only version of Array<T>
 */

// Definition
interface ReadonlyArray<T> {
  readonly length: number;
  readonly [n: number]: T;
  // ... other read-only methods
}

// Example usage
const numbers: ReadonlyArray<number> = [1, 2, 3];
numbers[0] = 4;  // Error: Index signature is readonly

// Convert to mutable
const mutable = [...numbers];

Source: TypeScript documentation via context7
```

### Test 4: Use Desktop Commander for File Operations

```
Use desktop-commander: List all TypeScript files in src/ directory
```

**Expected Response:**
```
TypeScript files in src/:

src/index.ts
src/components/Button.tsx
src/utils/helpers.ts
src/types/index.d.ts

Total: 4 files
```

### Test 5: Use Sequential Thinking for Code Planning

```
Use sequential-thinking: Plan refactoring of a React component from class to hooks
```

**Expected Response:**
```
Refactoring Plan: Class Component → Hooks

Step 1: Identify State Variables
- this.state → useState() hooks
- List all state properties

Step 2: Convert Lifecycle Methods
- componentDidMount → useEffect(() => {}, [])
- componentDidUpdate → useEffect(() => {}, [dependencies])
- componentWillUnmount → useEffect cleanup

Step 3: Extract Methods
- Class methods → regular functions or useCallback hooks
- Consider memoization with useMemo

Step 4: Update Event Handlers
- Remove `this` references
- Use arrow functions or useCallback

Step 5: Test & Validate
- Verify same behavior
- Check for missing dependencies
- Run tests

Reasoning provided by sequential-thinking MCP server
```

### Test 6: Code-Specific Enhancement

**Try a coding question and observe enhancement:**

**Your Prompt:**
```
regex for email validation
```

**Enhanced Prompt (by Qwen3-Coder):**
```typescript
// Email validation regex pattern

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Validates an email address
 * @param email - Email string to validate
 * @returns boolean - true if valid email format
 */
function validateEmail(email: string): boolean {
  return emailRegex.test(email);
}

// Example usage
validateEmail('user@example.com');  // true
validateEmail('invalid.email');      // false

// More comprehensive regex (RFC 5322 compliant)
const strictEmailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
```

**Note the enhancements:**
- Code-first response (TypeScript example)
- Includes file path context
- Minimal prose, maximum code
- Multiple variants provided

---

## Code-Optimized Features

### Qwen3-Coder Enhancement

VS Code clients automatically use **Qwen3-Coder:latest** for prompt enhancement (configured in `enhancement-rules.json`):

```json
{
  "vscode": {
    "model": "qwen3-coder:latest",
    "system_prompt": "Code-first responses. Include file paths. Minimal prose."
  }
}
```

**What This Means:**
- **Code-first formatting** - Always include code examples
- **File path preservation** - References like `src/components/Button.tsx` maintained
- **Minimal explanatory text** - Get to the code faster
- **Syntax highlighting** - Proper language detection

**Example Enhancement:**

**Original:**
```
how to sort array
```

**Enhanced (by Qwen3-Coder):**
```typescript
// src/utils/array-helpers.ts

// Sort array of numbers (ascending)
const numbers = [3, 1, 4, 1, 5, 9];
numbers.sort((a, b) => a - b);  // [1, 1, 3, 4, 5, 9]

// Sort array of strings
const fruits = ['banana', 'apple', 'cherry'];
fruits.sort();  // ['apple', 'banana', 'cherry']

// Sort array of objects
interface User {
  name: string;
  age: number;
}

const users: User[] = [
  { name: 'Alice', age: 30 },
  { name: 'Bob', age: 25 }
];

users.sort((a, b) => a.age - b.age);
```

### Workspace-Aware Configuration

AgentHub supports **per-project MCP configuration**:

**Project A (React):**
`.vscode/settings.json`:
```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Client-Name": "vscode-react-project"
      }
    }
  }
}
```

**Project B (Python):**
`.vscode/settings.json`:
```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Client-Name": "vscode-python-project"
      }
    }
  }
}
```

Then customize enhancement rules for each project in `enhancement-rules.json`:

```json
{
  "clients": {
    "vscode-react-project": {
      "model": "qwen3-coder:latest",
      "system_prompt": "React and TypeScript examples. Use hooks pattern."
    },
    "vscode-python-project": {
      "model": "qwen3-coder:latest",
      "system_prompt": "Python 3.11+ examples. Use type hints. Follow PEP 8."
    }
  }
}
```

### Fast Caching for Code Lookups

Code documentation lookups are cached aggressively:

- **First lookup**: ~2-3 seconds (fetch from context7)
- **Subsequent lookups**: <50ms (served from cache)

**Example:**
```
Use context7: React useState hook  ← ~2s (cache miss)
Use context7: React useState hook  ← <50ms (cache hit)
```

---

## Troubleshooting

### Issue: "MCP Server Not Connected"

**Symptoms:**
- Claude Code shows "Disconnected" status
- No MCP tools available
- Error in VS Code output panel

**Solutions:**

1. **Verify AgentHub is running:**
   ```bash
   curl http://localhost:9090/health
   # Should return: {"status": "healthy", ...}
   ```

2. **Check VS Code settings:**
   ```bash
   code ~/.vscode/settings.json
   # Verify "claude.mcp.servers.agenthub.url": "http://localhost:9090"
   ```

3. **Reload VS Code window:**
   - `Cmd+Shift+P` → "Developer: Reload Window"

4. **Check VS Code Output panel:**
   - View → Output → Select "Claude Code" or "Cline"
   - Look for connection errors

### Issue: "Timeout Errors"

**Symptoms:**
- MCP requests timeout after 30s
- Error: "Request to AgentHub timed out"

**Solutions:**

1. **Increase timeout in settings:**
   ```json
   {
     "claude.mcp.servers": {
       "agenthub": {
         "timeout": 60000
       }
     }
   }
   ```

2. **Check MCP server health:**
   ```bash
   curl http://localhost:9090/servers | jq '.[] | {name, status}'
   ```

3. **Restart slow servers:**
   ```bash
   curl -X POST http://localhost:9090/servers/context7/restart
   ```

### Issue: "Code Enhancement Not Working"

**Symptoms:**
- Responses don't include code examples
- Not using Qwen3-Coder style

**Solutions:**

1. **Verify Qwen3-Coder is installed:**
   ```bash
   ollama list | grep qwen3-coder
   # Should show: qwen3-coder:latest
   ```

2. **Pull Qwen3-Coder if missing:**
   ```bash
   ollama pull qwen3-coder:latest
   ```

3. **Check enhancement rules:**
   ```bash
   cat ~/.local/share/agenthub/configs/enhancement-rules.json | jq '.clients.vscode'
   ```

4. **Verify X-Client-Name header:**
   ```bash
   # Check AgentHub logs
   curl http://localhost:9090/dashboard/activity-partial | grep "vscode"
   ```

### Issue: "Desktop Commander Permission Errors"

**Symptoms:**
- File operations fail
- Error: "Permission denied"

**Solutions:**

1. **Grant VS Code Full Disk Access:**
   - System Settings → Privacy & Security → Full Disk Access
   - Add "Visual Studio Code"

2. **Check file permissions:**
   ```bash
   ls -la ~/path/to/file
   ```

3. **Run desktop-commander with correct permissions:**
   ```bash
   curl http://localhost:9090/servers/desktop-commander | jq '.status'
   ```

---

## Advanced Configuration

### Custom Enhancement Models

Override Qwen3-Coder with a different model:

```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "headers": {
        "X-Client-Name": "vscode-custom",
        "X-Enhancement-Model": "codellama:13b"
      }
    }
  }
}
```

Update `enhancement-rules.json`:
```json
{
  "clients": {
    "vscode-custom": {
      "model": "codellama:13b",
      "system_prompt": "Code examples with extensive comments"
    }
  }
}
```

### Disable Enhancement for Specific Projects

`.vscode/settings.json`:
```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "headers": {
        "X-Skip-Enhancement": "true"
      }
    }
  }
}
```

### Multiple MCP Endpoints

Combine AgentHub with direct MCP servers:

```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "transport": "http"
    },
    "local-memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "transport": "stdio"
    }
  }
}
```

---

## Performance Tips

### 1. Enable Workspace Caching

AgentHub caches responses per workspace:

```bash
# Check cache stats
curl http://localhost:9090/dashboard/stats-partial
```

### 2. Prefetch Common Documentation

Pre-warm the cache with common queries:

```bash
# Prefetch React docs
curl -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -d '{"method": "query", "params": {"library": "react"}}'

# Prefetch TypeScript docs
curl -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -d '{"method": "query", "params": {"library": "typescript"}}'
```

### 3. Monitor Response Times

Check dashboard for slow MCP servers:

```bash
open http://localhost:9090/dashboard
# Look for response time metrics
```

### 4. Optimize Ollama Performance

```bash
# Use smaller Qwen model for faster responses
ollama pull qwen3-coder:7b  # Instead of :latest (14b)

# Update enhancement-rules.json
{
  "vscode": {
    "model": "qwen3-coder:7b"
  }
}
```

---

## Keyboard Shortcuts

### Claude Code Shortcuts (macOS)

- `Cmd+Shift+P` → "Claude: Ask"
  Quick MCP query

- `Cmd+Shift+P` → "Claude: Show MCP Tools"
  List available MCP tools

- `Cmd+Shift+P` → "Claude: Clear Cache"
  Clear AgentHub cache

### Custom Keybindings

Add to `keybindings.json`:

```json
[
  {
    "key": "cmd+k cmd+m",
    "command": "claude.mcp.query",
    "when": "editorTextFocus"
  },
  {
    "key": "cmd+k cmd+d",
    "command": "claude.mcp.queryContext7",
    "args": "documentation"
  }
]
```

---

## See Also

- [app-configs.md](app-configs.md) - Quick config for all clients
- [claude-desktop-integration.md](claude-desktop-integration.md) - Claude Desktop setup
- [getting-started.md](getting-started.md) - AgentHub installation
- [keychain-setup.md](keychain-setup.md) - Credential management

---

## Quick Reference

### VS Code Settings Location

**Global:**
```
~/.vscode/settings.json
```

**Workspace:**
```
.vscode/settings.json
```

### AgentHub Health Check
```bash
curl http://localhost:9090/health
```

### View MCP Servers
```bash
curl http://localhost:9090/servers | jq
```

### Dashboard
```bash
open http://localhost:9090/dashboard
```

### Reload VS Code
```
Cmd+Shift+P → "Developer: Reload Window"
```
