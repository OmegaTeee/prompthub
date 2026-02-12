# LaunchAgent Setup Guide

> **For**: Running the PromptHub router as a background service on macOS

---

## Overview

A **LaunchAgent** makes the PromptHub router start automatically at login and keeps it running in the background.

**Without LaunchAgent:**
- You manually start the router every time
- If your Mac restarts, router is down
- Claude Desktop can't connect until you start it

**With LaunchAgent:**
- Router starts automatically at login
- Runs continuously in the background
- Survives Mac restarts
- Claude Desktop always has access to MCP servers

---

## Quick Setup

The LaunchAgent plist is already created in this repository:

**Template:** [`clients/launch_agents/com.prompthub.router.plist`](../clients/launch_agents/com.prompthub.router.plist)

### Installation Steps

```bash
# 1. Create logs directory
mkdir -p ~/.local/share/prompthub/logs

# 2. Copy plist to LaunchAgents directory
cp clients/launch_agents/com.prompthub.router.plist \
   ~/Library/LaunchAgents/

# 3. Load the LaunchAgent
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist

# 4. Verify it's running
curl http://localhost:9090/health
```

---

## Configuration Details

The LaunchAgent plist configures:

### Program
```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/visualval/.local/share/prompthub/.venv/bin/uvicorn</string>
    <string>router.main:app</string>
    <string>--host</string>
    <string>127.0.0.1</string>
    <string>--port</string>
    <string>9090</string>
    <string>--reload</string>
</array>
```

- **Command:** `uvicorn` from the virtual environment
- **App:** `router.main:app` (FastAPI application)
- **Host:** `127.0.0.1` (localhost only, secure)
- **Port:** `9090` (PromptHub default)
- **Reload:** Auto-reload on code changes

### Auto-Start & Resilience

```xml
<key>RunAtLoad</key>
<true/>

<key>KeepAlive</key>
<dict>
    <key>SuccessfulExit</key>
    <false/>
</dict>

<key>ThrottleInterval</key>
<integer>30</integer>
```

- **RunAtLoad:** Starts automatically at login
- **KeepAlive:** Restarts on crashes (but NOT on clean shutdown)
- **ThrottleInterval:** Waits 30 seconds before restarting (prevents rapid crash loops)

### Logging

```xml
<key>StandardOutPath</key>
<string>/Users/visualval/.local/share/prompthub/logs/router-stdout.log</string>

<key>StandardErrorPath</key>
<string>/Users/visualval/.local/share/prompthub/logs/router-stderr.log</string>
```

Logs are written to:
- **stdout:** `~/.local/share/prompthub/logs/router-stdout.log` (access logs, info)
- **stderr:** `~/.local/share/prompthub/logs/router-stderr.log` (errors, warnings)

### Environment

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/Users/visualval/.local/share/prompthub/.venv/bin:/opt/homebrew/bin:...</string>

    <key>PYTHONPATH</key>
    <string>/Users/visualval/.local/share/prompthub</string>
</dict>
```

- **PATH:** Includes virtual environment and Homebrew binaries
- **PYTHONPATH:** Set to project root for imports

---

## Managing the Service

### Check Status

```bash
# List all LaunchAgents (look for com.prompthub.router)
launchctl list | grep prompthub

# Check router health
curl http://localhost:9090/health
```

### Stop the Router

```bash
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist
```

### Start the Router

```bash
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```

### Restart the Router

```bash
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist && \
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```

### View Logs

```bash
# Standard output (access logs, info)
tail -f ~/.local/share/prompthub/logs/router-stdout.log

# Standard error (errors, warnings)
tail -f ~/.local/share/prompthub/logs/router-stderr.log

# Last 50 lines of both
tail -50 ~/.local/share/prompthub/logs/router-stderr.log
```

### Disable Auto-Start

```bash
# Unload and remove
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist
rm ~/Library/LaunchAgents/com.prompthub.router.plist
```

---

## Troubleshooting

### Router Not Starting

**Check if it's loaded:**

```bash
launchctl list | grep prompthub
# Expected: 6992  0  com.prompthub.router
```

If not listed:

```bash
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```

### "Label Already Exists"

```bash
# Unload first, then reload
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```

### Port 9090 Already in Use

```bash
# Find what's using port 9090
lsof -i :9090

# Kill the process if it's a stuck router
kill <PID>

# Then restart
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```

### Router Crashes Repeatedly

**Check error logs:**

```bash
tail -100 ~/.local/share/prompthub/logs/router-stderr.log
```

**Common causes:**

- **Ollama not running:** `brew install ollama && brew services start ollama`
- **Python dependencies missing:** `cd ~/.local/share/prompthub && source .venv/bin/activate && pip install -r requirements.txt`
- **Port conflict:** See "Port 9090 Already in Use" above
- **Permission issues:** `chmod 755 ~/.local/share/prompthub/logs`

### MCP Servers Not Starting

```bash
# Check server status
curl http://localhost:9090/servers | jq '.servers[] | {name, status, pid}'

# Start a specific server
curl -X POST http://localhost:9090/servers/<server-name>/start

# Check dashboard
open http://localhost:9090/dashboard
```

### Logs Growing Too Large

```bash
# Check log sizes
du -sh ~/.local/share/prompthub/logs/*

# Rotate logs (keep last 1000 lines)
tail -1000 ~/.local/share/prompthub/logs/router-stdout.log > /tmp/stdout.log
mv /tmp/stdout.log ~/.local/share/prompthub/logs/router-stdout.log

tail -1000 ~/.local/share/prompthub/logs/router-stderr.log > /tmp/stderr.log
mv /tmp/stderr.log ~/.local/share/prompthub/logs/router-stderr.log
```

---

## Updating the Configuration

If you need to change the plist (e.g., update paths, change port):

```bash
# 1. Edit the template
nano clients/launch_agents/com.prompthub.router.plist

# 2. Copy to LaunchAgents
cp clients/launch_agents/com.prompthub.router.plist \
   ~/Library/LaunchAgents/

# 3. Reload
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```

---

## Integration with Claude Desktop

Once the LaunchAgent is running, Claude Desktop can connect via the MCP bridge:

**Claude Desktop Config:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "prompthub": {
      "command": "node",
      "args": [
        "/Users/visualval/.local/share/prompthub/mcps/prompthub-bridge.js"
      ],
      "env": {
        "PROMPTHUB_URL": "http://localhost:9090",
        "CLIENT_NAME": "claude-desktop"
      }
    }
  }
}
```

The bridge connects to the router at `localhost:9090` and exposes all 8 MCP servers as tools.

---

## See Also

- **[keychain-setup.md](keychain-setup.md)** — Credential management for MCP servers
- **[claude-desktop-integration.md](claude-desktop-integration.md)** — Complete Claude Desktop setup
- **[testing-integrations.md](testing-integrations.md)** — Testing MCP server integrations

---

## Quick Reference

```bash
# Status
launchctl list | grep prompthub
curl http://localhost:9090/health

# Start
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist

# Stop
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist

# Restart
launchctl unload ~/Library/LaunchAgents/com.prompthub.router.plist && \
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist

# View logs
tail -f ~/.local/share/prompthub/logs/router-stderr.log

# Dashboard
open http://localhost:9090/dashboard
```
