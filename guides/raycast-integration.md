# Raycast Integration with AgentHub

> **Complete guide to connecting Raycast to AgentHub for action-oriented AI assistance**

---

## Overview

AgentHub provides **action-oriented MCP access** for Raycast, optimized for:

1. **Quick Actions** - Fast, concise responses under 200 words
2. **CLI Command Suggestions** - Terminal commands ready to copy-paste
3. **Documentation Lookup** - Instant API reference via context7
4. **File Operations** - Desktop Commander integration
5. **Reasoning Support** - Sequential thinking for planning

### Architecture

```
┌──────────────────┐
│    Raycast       │
│  (macOS Launcher)│
│                  │
│  X-Client-Name:  │
│   "raycast"      │
└────────┬─────────┘
         │ HTTP JSON-RPC
         ▼
┌─────────────────────────────────┐
│      AgentHub Router            │
│     localhost:9090              │
│                                 │
│  1. Action Enhancement          │
│     (DeepSeek-R1:latest)        │
│  2. CLI Command Focus           │
│  3. Under 200 Words             │
│  4. Fast Cache (< 100ms)        │
└────────┬────────────────────────┘
         │
         ├──────► context7 (quick docs)
         ├──────► desktop-commander (file ops)
         ├──────► sequential-thinking (planning)
         ├──────► fetch (web lookup)
         └──────► memory (quick recall)
```

---

## Prerequisites

- [ ] **Raycast installed**: Version 1.50+ with AI commands support
- [ ] **Raycast Pro subscription**: Required for AI features (or trial)
- [ ] **AgentHub running**: `curl http://localhost:9090/health` → healthy
- [ ] **Ollama with DeepSeek-R1**: `ollama pull deepseek-r1:latest`

---

## Example Configurations

AgentHub provides example configurations in `clients/raycast/`:

- **`raycast-mcp-servers.json.example`** - Example MCP server configuration for Raycast

**Quick copy:**
```bash
# Copy example to Raycast config directory
cp ~/.local/share/agenthub/clients/raycast/raycast-mcp-servers.json.example \
   ~/Library/Application\ Support/com.raycast.macos/mcp-servers.json
```

See [clients/raycast/README.md](../clients/raycast/README.md) for script commands and shortcuts.

---

## Installation Steps

### Step 1: Install Raycast (if needed)

```bash
# Download from website
open https://raycast.com

# Or via Homebrew
brew install --cask raycast
```

### Step 2: Enable Raycast AI Features

1. Open Raycast (`Cmd+Space` or custom hotkey)
2. Search for "AI Commands"
3. If not available, upgrade to Raycast Pro or start trial

### Step 3: Configure MCP Integration

Raycast supports MCP via **Raycast AI Commands** extension.

**Method A: Via Raycast UI (Recommended)**

1. Open Raycast
2. Search: "Extensions"
3. Navigate to: Settings → AI → MCP Servers
4. Click "Add MCP Server"
5. Fill in:
   - **Name**: `AgentHub`
   - **URL**: `http://localhost:9090`
   - **Transport**: HTTP
   - **Headers**: `X-Client-Name: raycast`
6. Save and enable

**Method B: Via Config File**

Create or edit Raycast MCP config:

```bash
# Create config directory
mkdir -p ~/Library/Application\ Support/com.raycast.macos/

# Create MCP servers config
cat > ~/Library/Application\ Support/com.raycast.macos/mcp-servers.json << 'EOF'
{
  "servers": [
    {
      "id": "agenthub",
      "name": "AgentHub",
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "headers": {
        "X-Client-Name": "raycast",
        "Content-Type": "application/json"
      },
      "retries": 3,
      "timeout": 15000
    }
  ]
}
EOF
```

**Method C: Via Script**

Download and run the setup script:

```bash
# Create setup script
cat > /tmp/raycast-setup.sh << 'SCRIPT'
#!/bin/bash

CONFIG_DIR="$HOME/Library/Application Support/com.raycast.macos"
CONFIG_FILE="$CONFIG_DIR/mcp-servers.json"

mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_FILE" ]; then
  echo "⚠️  Existing config found. Creating backup..."
  cp "$CONFIG_FILE" "$CONFIG_FILE.backup-$(date +%Y%m%d)"
fi

cat > "$CONFIG_FILE" << 'EOF'
{
  "servers": [
    {
      "id": "agenthub",
      "name": "AgentHub",
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "headers": {
        "X-Client-Name": "raycast"
      },
      "retries": 3,
      "timeout": 15000
    }
  ]
}
EOF

echo "✅ AgentHub configured for Raycast"
echo "🔄 Restart Raycast to apply changes"
SCRIPT

chmod +x /tmp/raycast-setup.sh
/tmp/raycast-setup.sh
```

### Step 4: Restart Raycast

```bash
# Quit Raycast
killall Raycast

# Reopen
open -a Raycast
```

---

## Verification & Testing

### Test 1: Check MCP Connection

1. Open Raycast (`Cmd+Space`)
2. Type: "AI Settings"
3. Navigate to: MCP Servers
4. Verify "AgentHub" shows: `✅ Connected (7 tools)`

### Test 2: Quick Documentation Lookup

In Raycast AI command:

```
context7: How to use curl for POST requests?
```

**Expected Response (under 200 words):**
```
# curl POST Request

Basic syntax:
curl -X POST https://api.example.com/endpoint

# With JSON data
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'

# With form data
curl -X POST https://api.example.com/login \
  -d "username=user&password=pass"

# With file upload
curl -X POST https://api.example.com/upload \
  -F "file=@/path/to/file.txt"

# With authentication
curl -X POST https://api.example.com/data \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"data": "value"}'

Common flags:
- -X POST  : HTTP method
- -H       : Add header
- -d       : Data payload
- -F       : Form upload
- -v       : Verbose output

Source: context7
```

### Test 3: File Operation via Desktop Commander

```
desktop-commander: List files in Downloads folder
```

**Expected Response:**
```
Files in ~/Downloads:

- presentation.pdf (4.2 MB)
- screenshot.png (1.8 MB)
- invoice-2024.pdf (234 KB)
- project.zip (15.3 MB)

Total: 4 files (21.5 MB)

Commands:
# Open Downloads folder
open ~/Downloads

# Sort by size
ls -lhS ~/Downloads
```

### Test 4: Quick Planning with Sequential Thinking

```
sequential-thinking: Plan a backup strategy for my Mac
```

**Expected Response:**
```
Mac Backup Strategy

Step 1: Choose Backup Methods
- Time Machine (incremental, local)
- Cloud (iCloud, Backblaze)
- Clone (Carbon Copy Cloner)

Step 2: Schedule Backups
- Daily: Time Machine
- Weekly: Cloud sync
- Monthly: Full clone

Step 3: Verify Regularly
- Test restore monthly
- Check backup logs

Commands:
# Enable Time Machine
tmutil enable

# Check backup status
tmutil listbackups
```

### Test 5: Action-Oriented CLI Suggestions

```
How do I find large files on my Mac?
```

**Expected Response (Raycast-optimized):**
```
Find Large Files on Mac

Quick command:
sudo du -h -d 1 ~ | sort -hr | head -20

Explanation:
- Lists 20 largest directories in home folder
- Human-readable sizes (-h)
- Sorted by size (-r)

Alternative (GUI):
open /Applications/Utilities/Disk\ Utility.app

Advanced find (files > 1GB):
find ~ -type f -size +1G -exec ls -lh {} \;

Recommended tools:
- DaisyDisk (visual disk usage)
- OmniDiskSweeper (free alternative)

Raycast built-in:
Search "Disk Usage" in Raycast
```

---

## Raycast-Optimized Features

### Action-Oriented Enhancement

Raycast prompts are automatically enhanced with **DeepSeek-R1:latest** using an action-oriented system prompt:

**Enhancement Configuration** (`enhancement-rules.json`):
```json
{
  "raycast": {
    "model": "deepseek-r1:latest",
    "system_prompt": "Action-oriented. Suggest CLI commands. Under 200 words."
  }
}
```

**What This Means:**
- **CLI commands first** - Always suggest terminal commands
- **Under 200 words** - Fast, scannable responses
- **Action verbs** - "Run X", "Open Y", "Try Z"
- **Copy-paste ready** - Commands formatted for terminal

**Example Enhancement:**

**Original Prompt:**
```
git branches
```

**Enhanced Response:**
```
Git Branch Management

# List all branches
git branch -a

# Create new branch
git checkout -b feature-name

# Switch branches
git checkout branch-name

# Delete branch
git branch -d branch-name

# Rename current branch
git branch -m new-name

# Push new branch
git push -u origin branch-name

Raycast tip: Use Raycast Git extension for visual branch switching
```

### Quick Commands Integration

Create custom Raycast commands that use AgentHub MCP:

**Script Command: "Ask Context7"**

Create: `~/Library/Application Support/com.raycast.macos/scripts/ask-context7.sh`

```bash
#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Ask Context7
# @raycast.mode fullOutput
# @raycast.packageName AgentHub
# @raycast.icon 📚
#
# @raycast.argument1 { "type": "text", "placeholder": "Query" }

QUERY="$1"

curl -s -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: raycast" \
  -d "{\"method\": \"query\", \"params\": {\"q\": \"$QUERY\"}}" \
  | jq -r '.result'
```

Make executable:
```bash
chmod +x ~/Library/Application\ Support/com.raycast.macos/scripts/ask-context7.sh
```

**Script Command: "List MCP Servers"**

Create: `~/Library/Application Support/com.raycast.macos/scripts/mcp-status.sh`

```bash
#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title MCP Server Status
# @raycast.mode fullOutput
# @raycast.packageName AgentHub
# @raycast.icon 🔌

curl -s http://localhost:9090/servers | jq -r '.[] | "\\(.name): \\(.status)"'
```

### Clipboard Integration

Raycast can automatically copy CLI commands to clipboard:

**Configure in `mcp-servers.json`:**
```json
{
  "servers": [
    {
      "id": "agenthub",
      "autoCopyCommands": true,
      "commandPrefix": "$"
    }
  ]
}
```

When AgentHub returns a CLI command, Raycast auto-copies it.

---

## Troubleshooting

### Issue: "MCP Server Not Found"

**Symptoms:**
- AgentHub not listed in Raycast AI settings
- No MCP tools available

**Solutions:**

1. **Verify config file:**
   ```bash
   cat ~/Library/Application\ Support/com.raycast.macos/mcp-servers.json
   ```
   Should be valid JSON.

2. **Check AgentHub is running:**
   ```bash
   curl http://localhost:9090/health
   ```

3. **Restart Raycast:**
   ```bash
   killall Raycast && sleep 2 && open -a Raycast
   ```

### Issue: "Connection Timeout"

**Symptoms:**
- Raycast AI commands hang
- Timeout after 15 seconds

**Solutions:**

1. **Increase timeout in config:**
   ```json
   {
     "servers": [{
       "timeout": 30000
     }]
   }
   ```

2. **Check MCP server status:**
   ```bash
   curl http://localhost:9090/servers | jq '.[] | {name, status}'
   ```

3. **Restart slow servers:**
   ```bash
   curl -X POST http://localhost:9090/servers/context7/restart
   ```

### Issue: "Responses Too Long"

**Symptoms:**
- Raycast responses exceed 200 words
- Hard to scan quickly

**Solutions:**

1. **Verify enhancement rules:**
   ```bash
   cat ~/.local/share/agenthub/configs/enhancement-rules.json | jq '.clients.raycast'
   ```
   Should have: `"Under 200 words"` in system prompt.

2. **Add response length limit:**
   Update `enhancement-rules.json`:
   ```json
   {
     "raycast": {
       "system_prompt": "Action-oriented. CLI commands only. Max 150 words. No explanations."
     }
   }
   ```

### Issue: "CLI Commands Not Highlighted"

**Symptoms:**
- Terminal commands not formatted properly
- Can't copy-paste easily

**Solutions:**

1. **Use code fences in responses:**
   Enhancement should wrap commands in ```bash blocks.

2. **Enable syntax highlighting in Raycast:**
   - Raycast Settings → AI → Enable Syntax Highlighting

3. **Update system prompt:**
   ```json
   {
     "system_prompt": "Wrap all CLI commands in ```bash code blocks"
   }
   ```

---

## Advanced Configuration

### Custom Client Name for Different Contexts

Create multiple Raycast profiles:

**Work Profile:**
```json
{
  "servers": [{
    "id": "agenthub-work",
    "headers": {
      "X-Client-Name": "raycast-work"
    }
  }]
}
```

**Personal Profile:**
```json
{
  "servers": [{
    "id": "agenthub-personal",
    "headers": {
      "X-Client-Name": "raycast-personal"
    }
  }]
}
```

Then customize enhancement rules:
```json
{
  "clients": {
    "raycast-work": {
      "system_prompt": "Professional tone. Corporate-approved commands only."
    },
    "raycast-personal": {
      "system_prompt": "Casual tone. All CLI commands allowed."
    }
  }
}
```

### Integrate with Raycast Workflows

Chain AgentHub with Raycast quicklinks:

**Quicklink: Search Docs**
```
Name: Search React Docs
URL: raycast://ai?prompt=context7%3A%20React%20{Query}
```

**Quicklink: File Search**
```
Name: Find Files
URL: raycast://ai?prompt=desktop-commander%3A%20Find%20{Query}
```

### Keyboard Shortcuts

Configure Raycast hotkeys:

1. Raycast Settings → Extensions → AI
2. Set hotkey for "AI Command" → `Cmd+Shift+A`
3. Set hotkey for "Ask AgentHub" → `Cmd+Shift+M`

---

## Performance Optimization

### Reduce Latency

1. **Use faster Ollama model:**
   ```bash
   ollama pull llama3.2:3b  # Faster than deepseek-r1:latest
   ```

   Update `enhancement-rules.json`:
   ```json
   {
     "raycast": {
       "model": "llama3.2:3b"
     }
   }
   ```

2. **Enable aggressive caching:**
   Raycast queries are often repeated, so caching helps significantly.

   ```bash
   # Check cache stats
   curl http://localhost:9090/dashboard/stats-partial
   ```

3. **Reduce timeout:**
   ```json
   {
     "timeout": 10000
   }
   ```

### Prefetch Common Queries

Pre-warm cache with frequent Raycast queries:

```bash
# Common CLI commands
curl -X POST http://localhost:9090/ollama/enhance \
  -H "X-Client-Name: raycast" \
  -d '{"prompt": "git commands"}'

curl -X POST http://localhost:9090/ollama/enhance \
  -H "X-Client-Name: raycast" \
  -d '{"prompt": "docker commands"}'

# Common docs
curl -X POST http://localhost:9090/mcp/context7/tools/call \
  -d '{"method": "query", "params": {"library": "node"}}'
```

---

## Raycast Extensions for AgentHub

### Recommended Extensions

**1. Git File History**
- Integrates with desktop-commander
- Quick file diffs and blame

**2. Terminal**
- Copy CLI commands directly from AI responses
- Execute in Raycast terminal

**3. Clipboard History**
- Store CLI commands for reuse
- Quick access to previous AgentHub responses

**4. System Monitor**
- Check if AgentHub is running
- View port 9090 status

### Creating Custom Extensions

Build a Raycast extension for AgentHub:

```typescript
// ~/Library/Application Support/com.raycast.macos/extensions/agenthub/src/index.tsx

import { Action, ActionPanel, List, showToast, Toast } from "@raycast/api";
import { useState, useEffect } from "react";

export default function Command() {
  const [servers, setServers] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:9090/servers")
      .then(res => res.json())
      .then(data => setServers(data))
      .catch(err => showToast(Toast.Style.Failure, "AgentHub unreachable"));
  }, []);

  return (
    <List>
      {servers.map(server => (
        <List.Item
          key={server.name}
          title={server.name}
          subtitle={server.status}
          accessories={[{ text: server.description }]}
          actions={
            <ActionPanel>
              <Action.OpenInBrowser url={`http://localhost:9090/servers/${server.name}`} />
            </ActionPanel>
          }
        />
      ))}
    </List>
  );
}
```

---

## See Also

- [app-configs.md](app-configs.md) - Quick config for all clients
- [claude-desktop-integration.md](claude-desktop-integration.md) - Claude Desktop setup
- [vscode-integration.md](vscode-integration.md) - VS Code / Cline setup
- [getting-started.md](getting-started.md) - AgentHub installation

---

## Quick Reference

### Raycast Config Location
```
~/Library/Application Support/com.raycast.macos/mcp-servers.json
```

### AgentHub Health Check
```bash
curl http://localhost:9090/health
```

### List MCP Servers
```bash
curl http://localhost:9090/servers | jq
```

### Restart Raycast
```bash
killall Raycast && open -a Raycast
```

### Test MCP Connection
```
Open Raycast → AI Settings → MCP Servers → AgentHub → ✅ Connected
```

### Example Queries

**Documentation:**
```
context7: TypeScript generics examples
```

**File Operations:**
```
desktop-commander: Find all .env files
```

**Planning:**
```
sequential-thinking: Plan weekly tasks
```

**Web Lookup:**
```
fetch: Get latest Hacker News headlines
```
