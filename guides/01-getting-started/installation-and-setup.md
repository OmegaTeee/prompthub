# AI Agent Hub: Getting Started Guide

> **For**: Non-programmers, end-users, and first-time setup

---

## Welcome!

You're about to set up the AI Agent Hub — a central hub that connects all your AI tools and makes them work better together.

**Good news:** You don't need programming knowledge. This guide walks you through every step.

**Setup time:** ~45 minutes (first time)

---

## Before You Start: Checklist

Make sure you have:

- [ ] Mac with M1/M2/M3 (or Intel, works either way)
- [ ] At least 8GB available RAM
- [ ] 20GB free disk space
- [ ] Claude Desktop installed (or VS Code, or Raycast)
- [ ] Administrator access to your Mac
- [ ] The router software (someone gave you this, or you built it from Phase 2)

---

## Phase 1: Installation (5 minutes)

### Step 1: Install Prerequisites

The router needs a few supporting tools. Copy-paste these commands into Terminal:

```bash
# Open Terminal
open -a Terminal

# 1. Install Homebrew (Mac's app installer)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Docker Desktop (or Colima for faster)
brew install colima
colima start
```

**What's happening:**

- Homebrew = Mac's app store
- Colima = lightweight container runner (where router lives)

**If something fails:** Don't worry, see **Troubleshooting** section at the end.

### Step 2: Create Router Directory

```bash
# Create a home for all router files
mkdir -p ~/.agenthub/logs
```

This creates a folder where everything will live.

### Step 3: Install the Router

Someone built the router for you. Get the installation files and run:

```bash
# Navigate to where you downloaded the router
cd ~/Downloads/agenthub

# Install it
./install.sh

# This should print: "✓ Router installed successfully at ~/.agenthub"
```

### Step 4: Verify Installation

```bash
# Check if everything is installed
curl http://localhost:9090/health

# Expected response: { "status": "ok" }
# If it fails, the router isn't running yet — that's normal
```

---

## Phase 2: Secure Credential Setup (10 minutes)

Your router needs API keys to work with Context7 (documentation) and other tools. We'll store them securely in macOS Keychain.

### Step 1: Gather Your API Keys

Get these from your accounts:

- **Context7 API Token** — from context7.example.com
- **Any other integrations** — collect these now

**Don't have keys yet?** That's OK. Skip this section, come back later.

### Step 2: Store in Keychain

Copy-paste these commands (replace `your-actual-key-here`):

```bash
# Store Context7 key securely
security add-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  -w "your-actual-context7-key-here" \
  ~/Library/Keychains/login.keychain-db

# Grant permanent access (click "Always Allow" when prompted)
security add-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  -w "your-actual-context7-key-here" \
  -A \
  ~/Library/Keychains/login.keychain-db
```

**What this does:**

- Stores your API key securely (encrypted)
- Allows the router to use it without you manually entering it
- `-A` flag = never ask again

**If you see a security prompt:** Click "Always Allow" → "OK"

---

## Phase 3: Background Service Setup (10 minutes)

### What This Does

Right now, you'd have to manually start the router every time you restart your Mac. This step makes it start automatically.

### Step 1: Create the Background Service

Copy-paste this entire block:

```bash
# Create the service configuration file
mkdir -p ~/.config/launchagents

cat > ~/.config/launchagents/com.agenthub.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agenthub.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>docker</string>
        <string>compose</string>
        <string>-f</string>
        <string>HOME_PLACEHOLDER/.agenthub/docker-compose.yml</string>
        <string>up</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>HOME_PLACEHOLDER/.agenthub/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>HOME_PLACEHOLDER/.agenthub/logs/stderr.log</string>
</dict>
</plist>
EOF

# Replace HOME_PLACEHOLDER with your actual home directory
sed -i '' "s|HOME_PLACEHOLDER|$HOME|g" ~/.config/launchagents/com.agenthub.plist

# Copy to system location
cp ~/.config/launchagents/com.agenthub.plist ~/Library/LaunchAgents/com.agenthub.plist

# Load it
launchctl load ~/Library/LaunchAgents/com.agenthub.plist

# Verify
launchctl list com.agenthub.service
```

**If the last command shows `com.agenthub.service` in the output:** ✅ Success!

### Step 2: Test That It's Running

```bash
# Wait 5 seconds for service to start
sleep 5

# Test connection
curl http://localhost:9090/health

# Expected output: { "status": "ok" }
```

**If you see `{ "status": "ok" }`:** ✅ Router is running!

**If you get "Connection refused":** See **Troubleshooting** below.

---

## Phase 4: Connect Your Apps (15 minutes)

Now we'll tell your apps where to find the router. Pick which apps you use:

### Claude Desktop

**If you use Claude Desktop:**

```bash
# 1. Create backup of current config
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup

# 2. Add router to config
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "agenthub": {
      "command": "localhost",
      "args": ["9090"],
      "type": "stdio",
      "disabled": false
    }
  }
}
EOF

# 3. Restart Claude Desktop
# Close it completely, then reopen it
```

**Verify:**

1. Open Claude Desktop
2. Look at bottom of chat window — should show AI Agent Hub badge
3. Try typing: "How do I use React hooks?"
4. Should get an answer

### VS Code

**If you use VS Code:**

```bash
# 1. Install Cline extension (if not already)
# Open VS Code → Extensions → Search "Cline" → Install

# 2. Open settings
code ~/.vscode/settings.json

# 3. Add this configuration (merge with existing content):
```

Then add this to the file:

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

**Verify:**

1. Close and reopen VS Code
2. Open Cline chat (sidebar)
3. Look for "Connected to agenthub" message
4. Try a prompt

### Raycast

**If you use Raycast:**

```bash
# 1. Create Raycast MCP config
mkdir -p ~/Library/Preferences/com.raycast.macos/

cat > ~/Library/Preferences/com.raycast.macos/mcpServers.json << 'EOF'
{
  "servers": [
    {
      "id": "agenthub",
      "name": AI Agent Hub,
      "url": "http://localhost:9090",
      "type": "http",
      "enabled": true,
      "timeout": 30000
    }
  ]
}
EOF

# 2. Restart Raycast
killall Raycast
sleep 2
open -a Raycast
```

**Verify:**

1. Open Raycast (`cmd+space`)
2. Search "ai"
3. Try an AI query

### Obsidian

**If you use Obsidian:**

First, install the MCP plugin:

1. Open Obsidian vault
2. Settings → Community Plugins
3. Search "MCP" → Install "MCP for Obsidian"
4. Enable it

Then create config:

```bash
# Replace /path/to/vault with your vault location
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
  }
}
EOF
```

**Verify:**

1. Restart Obsidian
2. Open Command Palette (`cmd+p`)
3. Search "MCP"
4. Should show connection status

---

## Phase 5: First Use (5 minutes)

### Try It Out

Pick one app and test:

**Claude Desktop:**

```
How do I implement error handling in Python?
```

**VS Code Cline:**

```
Create a simple React component
```

**Raycast:**

```
What's new in JavaScript 2024?
```

**Obsidian:**

```
Remember: I prefer TypeScript over JavaScript
```

### What Should Happen

- ✅ You get a response
- ✅ Response is relevant and specific
- ✅ No errors in the logs

### If Something Goes Wrong

Check **Troubleshooting** section below.

---

## What's Different Now?

### Before (Without Router)

- Set up each app separately
- Copy API keys multiple times
- Repeat yourself across conversations
- Pay full API cost

### After (With Router)

- ✅ All apps use same configuration
- ✅ Credentials stored securely once
- ✅ System remembers your preferences
- ✅ Saves API costs automatically

---

## Daily Usage

### Starting Your Day

**Router starts automatically.** Just open your apps and go.

No manual steps needed.

### Checking if Router is Running

```bash
# Quick check
curl http://localhost:9090/health

# Detailed status
launchctl list com.agenthub.service
```

### Stopping/Restarting Router

```bash
# Stop
launchctl stop com.agenthub.service

# Start
launchctl start com.agenthub.service

# Restart
launchctl stop com.agenthub.service && launchctl start com.agenthub.service
```

---

## Common Questions

### Q: Do I need to restart my Mac?

**A:** No, not required. But it doesn't hurt. Router will auto-start at next login if you do.

### Q: How do I update API keys later?

**A:** See **keychain-setup.md** for updating credentials.

### Q: How much disk space does it use?

**A:** ~2GB for local models. Without models, ~100MB.

### Q: Can I use this on multiple Macs?

**A:** Each Mac needs its own installation. Configurations are local.

### Q: What if I want to turn it off?

**A:** Run:

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.plist
```

### Q: Can I use Figma or ComfyUI with this?

**A:** Yes! See separate guides: **figma-integration.md** and **comfyui-integration.md** (coming soon).

---

## Next Steps: Optional Enhancements

### 1. Enable Prompt Enhancement (Week 2)

The router can automatically improve your prompts using local AI.

**Current state:** Works as-is
**Enhancement:** Automatic rephrasing for better answers

See: **advanced/launchagent-setup.md** for Ollama configuration.

### 2. Set Up Memory Server (Week 2)

The router can remember your preferences across conversations.

**Current state:** Works per-conversation
**Enhancement:** System-wide memory (remembers you prefer TypeScript, async/await, etc.)

See: **advanced/keychain-setup.md** for memory configuration.

### 3. Enable Context7 (Week 3)

Automatic documentation fetching for libraries (React, Node, Python, etc.).

**Current state:** You describe what you need
**Enhancement:** Say "Use context7: React hooks" → Gets real docs automatically

See: **advanced/app-configs.md** for context7 setup.

---

## Troubleshooting

### "Connection refused" On `curl http://localhost:9090/health`

**Problem:** Router isn't running

**Solution:**

```bash
# Check if service is loaded
launchctl list com.agenthub.service

# Should output a dict with service info

# If not found, reload it:
launchctl load ~/Library/LaunchAgents/com.agenthub.plist

# Check logs for errors
tail -50 ~/.agenthub/logs/stderr.log
```

### "Port 9090 Already in use"

**Problem:** Something else is using the port

**Solution:**

```bash
# Find what's using port 9090
lsof -i :9090

# Kill it (if safe)
kill -9 <PID>

# Or use different port (advanced users only)
```

### "Keychain Permission denied"

**Problem:** Router can't access stored credentials

**Solution:**

```bash
# Unlock Keychain
security unlock-keychain ~/Library/Keychains/login.keychain-db

# Restart router
launchctl restart com.agenthub.service
```

### App says "MCP Server not responding"

**Problem:** Router crashed or is slow

**Solution:**

```bash
# Check if running
ps aux | grep agenthub

# Restart it
launchctl restart com.agenthub.service

# Check for errors
tail -100 ~/.agenthub/logs/stderr.log

# Common causes:
# - Ollama not installed (if using prompt enhancement)
# - Out of disk space
# - Out of memory
```

### "Keychain Item not found"

**Problem:** You haven't stored API keys yet

**Solution:**

1. Go back to **Phase 2: Secure Credential Setup**
2. Run the `security add-generic-password` commands
3. Replace `your-actual-key-here` with real keys

### macOS Asks "Allow Keychain Access?" Every Time

**Problem:** Permissions not fully set

**Solution:**

```bash
# Re-add with -A flag (always allow)
security add-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  -w "your-key" \
  -U -A \
  ~/Library/Keychains/login.keychain-db
```

Or manually via Keychain Access app:

1. Open `/Applications/Utilities/Keychain Access.app`
2. Find `agenthub-*` items
3. Double-click → "Access Control" tab
4. Set to "Allow all applications"

### "Docker Not found"

**Problem:** Docker/Colima not installed

**Solution:**

```bash
# Install Colima
brew install colima

# Start it
colima start

# Verify
colima status
```

### Nothing in logs, router just won't start

**Problem:** Complex issue

**Solution:**

1. Manually start the router to see errors:

```bash
cd ~/.agenthub
docker compose -f docker-compose.yml up
```

1. Watch the output — it will show what's wrong
2. Post error output to your builder for help

---

## Getting Help

### If You Get Stuck

1. **Check logs first:**

```bash
tail -100 ~/.agenthub/logs/stderr.log
```

1. **Verify basics:**

```bash
# Is service loaded?
launchctl list com.agenthub.service

# Is Docker running?
docker ps

# Is port free?
lsof -i :9090
```

1. **Restart everything:**

```bash
launchctl restart com.agenthub.service
sleep 3
curl http://localhost:9090/health
```

1. **Contact your builder** with:
   - What you were trying to do
   - What happened instead
   - Last 100 lines of logs:

```bash
tail -100 ~/.agenthub/logs/stderr.log
```

---

## Advanced: Understanding the Architecture

### What Just Happened (Simplified)

```
Your Mac starts
    ↓
LaunchAgent automatically starts router (in background)
    ↓
Router listens at localhost:9090
    ↓
You open Claude Desktop, VS Code, etc.
    ↓
These apps connect to router at localhost:9090
    ↓
Router receives request, improves it, routes to right tool
    ↓
Tool returns answer
    ↓
You see better response
```

### The Three Parts

1. **LaunchAgent** — Keeps router running 24/7
2. **Router** — Central hub (localhost:9090)
3. **App Configs** — Tell each app where router is

You've successfully set all three up. ✅

---

## What's Next?

### Week 1: Comfort

- Use router normally
- Get comfortable with setup
- Notice improvements in answer quality

### Week 2: Optimization

- Set up API key rotation (security)
- Enable prompt enhancement (better answers)
- Configure memory server (persistent context)

### Week 3+: Integration

- Add Figma integration (design workflows)
- Add ComfyUI integration (image generation)
- Build custom MCP servers for your workflow

---

## Success Checklist

Before you call setup "done," verify:

- [ ] `curl http://localhost:9090/health` returns `{ "status": "ok" }`
- [ ] At least one app (Claude, VS Code, Raycast, or Obsidian) shows AI Agent Hub connected
- [ ] You can send a prompt and get a response
- [ ] Router starts automatically after Mac restart
- [ ] No errors in `~/.agenthub/logs/stderr.log`

If all checked: ✅ **Setup is complete!**

---

## See Also

**For more details:**

- **keychain-setup.md** — Advanced credential management
- **launchagent-setup.md** — Background service customization
- **app-configs.md** — Per-app configuration details
- **comparison-table.md** — Why AI Agent Hub vs alternatives

**Coming soon:**

- **figma-integration.md** — Design-to-code workflows
- **comfyui-integration.md** — Image generation workflows
