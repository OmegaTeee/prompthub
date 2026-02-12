
# App Configurations Guide

> **For**: Connecting Claude Desktop, VS Code, Raycast, and Obsidian to the AI Agent Hub

---

## Overview

Each app needs minimal configuration to connect to the router at `localhost:9090`. Most apps use standardized MCP configuration files.

**What gets configured:**
- Router URL: `localhost:9090`
- MCP server reference (built into router)
- Optional: app-specific settings (timeouts, retries, etc.)

---

## Claude Desktop

### Location
`~/Library/Application Support/Claude/claude_desktop_config.json`

### Configuration

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

### Setup Steps

1. **Get your Claude Desktop config file:**
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. **Add the router MCP server** (merge with existing config):
```bash
# Create backup
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup

# Use `jq` to merge new server (or edit manually)
jq '.mcpServers.agenthub = {
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
}' ~/Library/Application\ Support/Claude/claude_desktop_config.json > /tmp/config.json && \
mv /tmp/config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

3. **Restart Claude Desktop**

4. **Verify in Claude:**
   - Open Claude Desktop
   - Look for "AI Agent Hub" badge at bottom of chat
   - Try a prompt: "Use context7: How do I use React hooks?"

---

## VS Code

### Location
`~/.vscode/settings.json` or `.vscode/settings.json` (workspace)

### Configuration

```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "command": "localhost:9090",
      "type": "http",
      "disabled": false
    }
  },
  "claude.mcp.autoConnect": true,
  "claude.mcp.timeout": 30000
}
```

### Setup Steps

1. **Install Cline extension** (if not already):
   - VS Code Extensions → Search "Cline"
   - Install official Cline extension

2. **Open settings:**
```bash
# Global settings
code ~/.vscode/settings.json
  
# Or for current workspace
code .vscode/settings.json
```

3. **Add AI Agent Hub configuration:**
```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "command": "localhost:9090",
      "type": "http",
      "disabled": false
    }
  }
}
```

4. **Restart VS Code**

5. **Verify in Cline:**
   - Open Cline chat in sidebar
   - Look for "Connected to agenthub" message
   - Try command: "Use context7: Node.js fs module documentation"

### Workspace Config

For project-specific MCP config, create `.vscode/settings.json`:

```json
{
  "claude.mcp.servers": {
    "agenthub": {
      "command": "localhost:9090",
      "type": "http"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "vscode.typescript-language-features"
  }
}
```

---

## Raycast

### Location
`~/Library/Preferences/com.raycast.macos/mcpServers.json`

### Configuration

```json
{
  "servers": [
    {
      "id": "agenthub",
      "name": "AI Agent Hub",
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "retries": 3,
      "timeout": 30000
    }
  ]
}
```

### Setup Steps

1. **Open Raycast preferences:**
   - Raycast Menu → Preferences
   - Or: `cmd+,` in Raycast

2. **Navigate to Extensions:**
   - Extensions → AI → MCP Servers

3. **Add AI Agent Hub:**
   - Click "Add Server"
   - Name: "AI Agent Hub"
   - URL: `http://localhost:9090`
   - Type: HTTP
   - Save

4. **Or edit config directly:**
```bash
mkdir -p ~/Library/Preferences/com.raycast.macos/
cat > ~/Library/Preferences/com.raycast.macos/mcpServers.json << 'EOF'
{
  "servers": [
    {
      "id": "agenthub",
      "name": "AI Agent Hub",
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "retries": 3,
      "timeout": 30000
    }
  ]
}
EOF
```

5. **Restart Raycast:**
```bash
killall Raycast
open -a Raycast
```

6. **Verify:**
   - Open Raycast (`cmd+space`)
   - Search "ai"
   - Try an AI query
   - Should show AI Agent Hub as available

---

## Obsidian

### Location
`<your-vault>/.obsidian/mcp.json`

### Configuration

```json
{
  "servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "timeout": 30000
    }
  },
  "autoConnect": true,
  "enableCaching": true,
  "cacheTTL": 3600
}
```

### Setup Steps

1. **Open Obsidian vault settings:**
   - Settings → Community Plugins (if needed, enable developer mode)
   - Install "MCP for Obsidian" plugin (search community plugins)

2. **Configure MCP in settings:**
   - Settings → MCP → Add Server
   - Name: "agenthub"
   - URL: `http://localhost:9090`
   - Type: HTTP
   - Save

3. **Or edit config manually:**
```bash
# Find your Obsidian vault path
VAULT_PATH="$HOME/path/to/your/vault"

cat > "$VAULT_PATH/.obsidian/mcp.json" << 'EOF'
{
  "servers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "timeout": 30000
    }
  },
  "autoConnect": true,
  "enableCaching": true
}
EOF
```

4. **Restart Obsidian**

5. **Verify:**
   - Open Command Palette: `cmd+p`
   - Type "AI Agent Hub"
   - Should show connection status
   - Try: "MCP: Memory recall my preferences"

---

## Configuration Templates

### Full Config Template (All Apps)

**For easy setup, here's a unified template:**

```bash
#!/bin/bash

echo "=== AI Agent Hub Configuration Setup ==="

# 1. Claude Desktop
echo "Configuring Claude Desktop..."
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -f "$CLAUDE_CONFIG" ]; then
  jq '.mcpServers.agenthub = {
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
  }' "$CLAUDE_CONFIG" > /tmp/claude.json && mv /tmp/claude.json "$CLAUDE_CONFIG"
  echo "✓ Claude Desktop configured"
else
  echo "✗ Claude Desktop config not found"
fi

# 2. VS Code
echo "Configuring VS Code..."
VSCODE_CONFIG="$HOME/.vscode/settings.json"
mkdir -p "$HOME/.vscode"
if [ ! -f "$VSCODE_CONFIG" ]; then
  echo '{}' > "$VSCODE_CONFIG"
fi
jq '.claude.mcp.servers.agenthub = {
  "command": "localhost:9090",
  "type": "http",
  "disabled": false
}' "$VSCODE_CONFIG" > /tmp/vscode.json && mv /tmp/vscode.json "$VSCODE_CONFIG"
echo "✓ VS Code configured"

# 3. Raycast
echo "Configuring Raycast..."
RAYCAST_DIR="$HOME/Library/Preferences/com.raycast.macos"
mkdir -p "$RAYCAST_DIR"
cat > "$RAYCAST_DIR/mcpServers.json" << 'EOF'
{
  "servers": [
    {
      "id": "agenthub",
      "name": "AI Agent Hub",
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "retries": 3,
      "timeout": 30000
    }
  ]
}
EOF
echo "✓ Raycast configured"

# 4. Obsidian (manual after this)
echo "✓ For Obsidian: See manual steps in app-configs.md"

echo ""
echo "=== Setup Complete ==="
echo "All apps are now configured to use AI Agent Hub at localhost:9090"
echo "Restart each app for changes to take effect"
```

---

## Common Configuration Issues

### "Connection Refused" (localhost:9090)

**Problem**: App can't connect to router

**Solutions:**
```bash
# Check if router is running
lsof -i :9090

# Start router (or LaunchAgent)
launchctl start com.agenthub.service

# Or manually start
docker compose -f ~/.agenthub/docker-compose.yml up -d
```

### MCP Server Not Appearing in App

**Problem**: Router configured but app doesn't show "AI Agent Hub" indicator

**Solution:**
1. Verify `localhost:9090` is correct in config
2. Test connection: `curl http://localhost:9090/health`
3. Restart the app completely
4. Check app logs for MCP-related errors

### "Timeout" Or "Slow Response"

**Problem**: MCP requests taking too long

**Solution:**
1. Increase timeout in config: `"timeout": 60000` (60 seconds)
2. Check if Ollama/router is under heavy load: `top`
3. Check network latency: `ping localhost`

### Keychain Permission Prompts

**Problem**: Constant "Allow Keychain access?" prompts

**Solution:**
1. Grant always-allow via Keychain Access app
2. Or use separate unlocked keychain (see launchagent-setup.md)

---

## Per-App Tips

### Claude Desktop Tips

- **Multiple MCP servers**: Add more items to `mcpServers` dict
- **Disable server**: Set `"disabled": true`
- **alwaysAllow**: Pre-approve resource access without prompts

### VS Code Tips

- **Workspace-specific config**: Edit `.vscode/settings.json` in project
- **Global config**: Edit `~/.vscode/settings.json`
- **Cline extension required**: Make sure Cline is installed

### Raycast Tips

- **Quick MCP access**: Raycast theme supports MCP queries directly
- **Custom actions**: Combine MCP with Raycast script actions
- **Terminal integration**: Use Raycast terminal window with MCP

### Obsidian Tips

- **Per-vault config**: Each Obsidian vault has its own `.obsidian/mcp.json`
- **Plugin required**: Install "MCP for Obsidian" community plugin first
- **Memory persistence**: Obsidian vault acts as permanent note store

---

## Verification Checklist

After configuring, verify each app:

- [ ] **Claude Desktop**
  - [ ] Opens without errors
  - [ ] AI Agent Hub badge visible at bottom
  - [ ] Can issue AI query

- [ ] **VS Code**
  - [ ] Cline extension installed
  - [ ] Can open Cline chat panel
  - [ ] Cline shows "Connected to agenthub"

- [ ] **Raycast**
  - [ ] Raycast opens normally
  - [ ] Can search for AI commands
  - [ ] AI Agent Hub available in command palette

- [ ] **Obsidian**
  - [ ] Vault opens normally
  - [ ] MCP plugin shows connection status
  - [ ] Can execute MCP commands via command palette

---

## See Also

- **keychain-setup.md** — Credential management
- **launchagent-setup.md** — Background service setup
- **comparison-table.md** — AI Agent Hub vs alternatives

