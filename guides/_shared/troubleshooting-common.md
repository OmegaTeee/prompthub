# Common Troubleshooting Guide

**Purpose:** Centralized solutions for issues that affect all AgentHub users, regardless of which client they're using.

> **What you'll learn:** How to diagnose and fix the most common AgentHub problems, from connection failures to MCP server crashes.

---

## Quick Diagnostic Checklist

Before diving into specific issues, run these quick checks:

```bash
# 1. Is AgentHub running?
curl http://localhost:9090/health

# 2. Are MCP servers responding?
curl http://localhost:9090/servers

# 3. Is Ollama running (if using enhancement)?
curl http://localhost:11434/api/version

# 4. Check recent logs
tail -20 ~/Library/Logs/agenthub-router.log
```

If all four checks pass, your issue is likely client-specific. See the troubleshooting section in your client's integration guide.

---

## Connection Issues

### Issue: "Cannot connect to AgentHub"

**Symptoms:**
- Client shows "Connection refused" or "Network error"
- `curl http://localhost:9090/health` fails
- Dashboard won't load

**Diagnosis:**

```bash
# Check if AgentHub is running
ps aux | grep "uvicorn router.main:app"

# Check if port 9090 is in use
lsof -i :9090
```

**Solutions:**

#### Solution 1: Start AgentHub manually

```bash
cd ~/.local/share/agenthub
source .venv/bin/activate
uvicorn router.main:app --host 0.0.0.0 --port 9090
```

**If this works:** LaunchAgent needs to be fixed (see Solution 2)

#### Solution 2: Fix LaunchAgent (macOS)

```bash
# Check LaunchAgent status
launchctl list | grep com.agenthub.router

# Restart LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist

# Verify it started
launchctl list | grep com.agenthub.router
```

#### Solution 3: Check for port conflicts

```bash
# See what's using port 9090
lsof -i :9090

# If another process is using it, either:
# A) Kill that process (use with caution)
kill -9 <PID>

# B) Or change AgentHub's port in .env
echo "PORT=9091" >> ~/.local/share/agenthub/.env
```

---

### Issue: "AgentHub starts then immediately stops"

**Symptoms:**
- Process appears briefly then disappears
- Health check fails after restart
- Logs show Python errors

**Diagnosis:**

```bash
# Check recent logs for errors
tail -50 ~/Library/Logs/agenthub-router.log

# Try starting manually to see error messages
cd ~/.local/share/agenthub
source .venv/bin/activate
uvicorn router.main:app --reload --port 9090
```

**Common causes & solutions:**

#### Cause 1: Missing Python dependencies

```bash
cd ~/.local/share/agenthub
source .venv/bin/activate
pip install -r requirements.txt
```

#### Cause 2: Corrupted virtual environment

```bash
cd ~/.local/share/agenthub
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Cause 3: Invalid configuration file

```bash
# Validate JSON syntax
python3 -m json.tool configs/mcp-servers.json
python3 -m json.tool configs/enhancement-rules.json

# If invalid, restore from backup or example
cp configs/mcp-servers.json.example configs/mcp-servers.json
```

---

### Issue: "Slow or intermittent connections"

**Symptoms:**
- Requests timeout occasionally
- Dashboard loads slowly
- Client shows "Request timed out"

**Diagnosis:**

```bash
# Check response times
time curl http://localhost:9090/health

# Check system resource usage
ps aux | grep "uvicorn router.main:app"

# Check for network issues
ping localhost
```

**Solutions:**

#### Solution 1: Increase timeout settings
Edit `.env`:

```bash
REQUEST_TIMEOUT=30  # Increase from default 10s
MCP_SERVER_TIMEOUT=20  # Increase from default 10s
```

#### Solution 2: Check Ollama performance (if using enhancement)

```bash
# Test Ollama response time
time curl http://localhost:11434/api/version

# If slow, restart Ollama
pkill -f ollama
ollama serve &
```

#### Solution 3: Clear cache and restart

```bash
# Stop AgentHub
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist

# Clear cache (if using external cache)
redis-cli FLUSHALL  # Only if using Redis

# Restart
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

## MCP Server Issues

### Issue: "MCP server not found"

**Symptoms:**
- Client shows "Server 'filesystem' not found"
- `curl http://localhost:9090/servers` doesn't list expected server
- Dashboard shows empty server list

**Diagnosis:**

```bash
# Check configured servers
cat ~/.local/share/agenthub/configs/mcp-servers.json

# Verify MCP server packages are installed
cd ~/.local/share/agenthub/mcps
npm list
```

**Solutions:**

#### Solution 1: Add server to config
Edit `configs/mcp-servers.json`:

```json
{
  "servers": {
    "filesystem": {
      "command": "node",
      "args": ["mcps/filesystem/dist/index.js"],
      "auto_start": true,
      "restart_on_failure": true
    }
  }
}
```

#### Solution 2: Install missing MCP server packages

```bash
cd ~/.local/share/agenthub/mcps
npm install @modelcontextprotocol/server-filesystem
npm install @modelcontextprotocol/server-fetch
npm install @modelcontextprotocol/server-brave-search
```

#### Solution 3: Restart AgentHub to reload config

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

### Issue: "MCP server keeps crashing"

**Symptoms:**
- Server status shows "stopped" repeatedly
- Circuit breaker shows "OPEN"
- Logs show MCP server errors

**Diagnosis:**

```bash
# Check MCP server logs
tail -100 ~/Library/Logs/agenthub-router.log | grep "MCP server"

# Check server status
curl http://localhost:9090/servers

# Try starting server manually
curl -X POST http://localhost:9090/servers/filesystem/start
```

**Solutions:**

#### Solution 1: Check for missing credentials

```bash
# For brave-search server
security find-generic-password -s "agenthub.brave_api_key" -w

# For other API-key-requiring servers
security find-generic-password -s "agenthub.CREDENTIAL_NAME" -w

# If missing, add credentials
security add-generic-password \
  -s "agenthub.brave_api_key" \
  -a "agenthub" \
  -w "YOUR_API_KEY"
```

#### Solution 2: Check Node.js version

```bash
node --version  # Should be 20.x or higher

# If wrong version, install correct one
brew install node@20
brew link node@20
```

#### Solution 3: Rebuild MCP server

```bash
cd ~/.local/share/agenthub/mcps/filesystem
npm install
npm run build
```

---

### Issue: "Circuit breaker is OPEN"

**Symptoms:**
- Requests return "Circuit breaker OPEN for server 'X'"
- Dashboard shows red status for server
- Server appears to be working but requests are blocked

**Diagnosis:**

```bash
# Check circuit breaker status in dashboard
open http://localhost:9090/dashboard

# Check failure count in logs
tail -100 ~/Library/Logs/agenthub-router.log | grep "circuit"
```

**Solutions:**

#### Solution 1: Wait for automatic recovery (30 seconds)
The circuit breaker will automatically attempt to recover after 30 seconds. Check dashboard for state change from OPEN → HALF_OPEN → CLOSED.

#### Solution 2: Fix underlying issue causing failures

```bash
# Check what's causing failures
tail -100 ~/Library/Logs/agenthub-router.log | grep "ERROR"

# Common causes:
# - Missing credentials
# - MCP server crashed
# - Network issues
# - Invalid requests
```

#### Solution 3: Manually restart server to reset circuit breaker

```bash
# Stop server
curl -X POST http://localhost:9090/servers/filesystem/stop

# Wait 5 seconds
sleep 5

# Start server
curl -X POST http://localhost:9090/servers/filesystem/start

# Verify it's running
curl http://localhost:9090/servers
```

---

## Enhancement Issues

### Issue: "Enhancement not working"

**Symptoms:**
- Prompts are not being enhanced
- Client receives unenhanced responses
- Enhancement metrics in dashboard show 0

**Diagnosis:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Test enhancement directly
curl -X POST http://localhost:9090/ollama/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: test-client" \
  -d '{"prompt": "test", "model": "llama3.2"}'

# Check enhancement rules config
cat ~/.local/share/agenthub/configs/enhancement-rules.json
```

**Solutions:**

#### Solution 1: Start Ollama

```bash
# Start Ollama service
ollama serve &

# Verify it's running
curl http://localhost:11434/api/version

# Pull required models
ollama pull llama3.2
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
```

#### Solution 2: Enable enhancement in client config
For Claude Desktop, edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Enhance": "true",
        "X-Client-Name": "claude-desktop"
      }
    }
  }
}
```

#### Solution 3: Configure enhancement rules
Edit `configs/enhancement-rules.json`:

```json
{
  "claude-desktop": {
    "model": "deepseek-r1:7b",
    "system_prompt": "Provide structured reasoning responses",
    "enabled": true
  }
}
```

---

### Issue: "Enhancement is slow"

**Symptoms:**
- Requests take > 5 seconds
- Client timeouts
- High CPU usage

**Diagnosis:**

```bash
# Test enhancement speed
time curl -X POST http://localhost:9090/ollama/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: test-client" \
  -d '{"prompt": "test", "model": "llama3.2"}'

# Check Ollama performance
time ollama run llama3.2 "test"

# Check system resources
top -o cpu
```

**Solutions:**

#### Solution 1: Use faster models
Edit `configs/enhancement-rules.json`:

```json
{
  "claude-desktop": {
    "model": "llama3.2",  // Faster than deepseek-r1:70b
    "enabled": true
  }
}
```

#### Solution 2: Disable enhancement for quick tasks
In client config, set:

```json
{
  "headers": {
    "X-Enhance": "false"  // Disable for speed
  }
}
```

#### Solution 3: Increase Ollama performance

```bash
# Add GPU acceleration (if available)
export OLLAMA_NUM_GPU=1

# Increase context size if needed
export OLLAMA_NUM_CTX=2048

# Restart Ollama
pkill -f ollama
ollama serve &
```

---

## Credential & Security Issues

### Issue: "API key not found"

**Symptoms:**
- MCP server returns "Authentication failed"
- Logs show "Credential not found in Keychain"
- Client shows "API key error"

**Diagnosis:**

```bash
# Check if credential exists
security find-generic-password -s "agenthub.brave_api_key" -w

# List all AgentHub credentials
security dump-keychain | grep agenthub
```

**Solutions:**

#### Solution 1: Add missing credential

```bash
# Add API key to Keychain
security add-generic-password \
  -s "agenthub.brave_api_key" \
  -a "agenthub" \
  -w "YOUR_API_KEY_HERE"

# Verify it was added
security find-generic-password -s "agenthub.brave_api_key" -w
```

#### Solution 2: Update existing credential

```bash
# Delete old credential
security delete-generic-password -s "agenthub.brave_api_key"

# Add new one
security add-generic-password \
  -s "agenthub.brave_api_key" \
  -a "agenthub" \
  -w "NEW_API_KEY_HERE"
```

#### Solution 3: Check credential naming
Ensure credential names follow the pattern: `agenthub.CREDENTIAL_NAME`

Common credential keys:
- `agenthub.brave_api_key` - Brave Search API
- `agenthub.openai_api_key` - OpenAI API (if using OpenAI mode)
- `agenthub.anthropic_api_key` - Anthropic API (if needed)

---

### Issue: "Permission denied accessing Keychain"

**Symptoms:**
- Logs show "Keychain access denied"
- First run asks for Keychain password repeatedly
- Security alert popups

**Diagnosis:**

```bash
# Check Keychain access
security find-generic-password -s "agenthub.brave_api_key"

# Check if Keychain is locked
security show-keychain-info
```

**Solutions:**

#### Solution 1: Unlock Keychain

```bash
# Unlock login keychain
security unlock-keychain ~/Library/Keychains/login.keychain-db

# Or unlock in Keychain Access app
open -a "Keychain Access"
```

#### Solution 2: Grant Python access to Keychain
1. Open **Keychain Access** app
2. Find any "agenthub.*" credential
3. Right-click → **Get Info**
4. Go to **Access Control** tab
5. Click **+** and add `/usr/bin/python3`
6. Click **Save Changes**

#### Solution 3: Allow AgentHub always
In Keychain Access:
1. Select credential
2. **Access Control** → Choose "Allow all applications to access this item"
3. Enter your password to confirm

---

## Log & Monitoring Issues

### Issue: "Can't find logs"

**Symptoms:**
- Log files missing
- Can't diagnose issues
- Empty log directory

**Diagnosis:**

```bash
# Check log directory
ls -la ~/Library/Logs/ | grep agenthub

# Check LaunchAgent log configuration
cat ~/Library/LaunchAgents/com.agenthub.router.plist | grep -A2 "Log"
```

**Solutions:**

#### Solution 1: Create log directory

```bash
mkdir -p ~/Library/Logs
```

#### Solution 2: Check LaunchAgent log paths
Ensure LaunchAgent plist has correct log paths:

```xml
<key>StandardOutPath</key>
<string>/Users/YOUR_USERNAME/Library/Logs/agenthub-router.log</string>
<key>StandardErrorPath</key>
<string>/Users/YOUR_USERNAME/Library/Logs/agenthub-router-error.log</string>
```

#### Solution 3: Restart LaunchAgent to create logs

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist

# Verify logs are being written
tail -f ~/Library/Logs/agenthub-router.log
```

---

### Issue: "Dashboard shows no data"

**Symptoms:**
- Dashboard loads but shows empty lists
- No activity log
- No MCP server status

**Diagnosis:**

```bash
# Check if dashboard endpoint is working
curl http://localhost:9090/dashboard

# Check if activity log database exists
ls -la ~/.local/share/agenthub/data/

# Check dashboard logs
tail -50 ~/Library/Logs/agenthub-router.log | grep dashboard
```

**Solutions:**

#### Solution 1: Create data directory

```bash
mkdir -p ~/.local/share/agenthub/data
```

#### Solution 2: Initialize activity log database

```bash
cd ~/.local/share/agenthub
source .venv/bin/activate
python3 -c "from router.middleware.activity_logging import init_db; import asyncio; asyncio.run(init_db())"
```

#### Solution 3: Restart AgentHub

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

## Configuration Issues

### Issue: "Config file changes not taking effect"

**Symptoms:**
- Edited `mcp-servers.json` but changes ignored
- New enhancement rules not applied
- Old config still active

**Diagnosis:**

```bash
# Check if config file has syntax errors
python3 -m json.tool ~/.local/share/agenthub/configs/mcp-servers.json

# Check when config was last modified
ls -la ~/.local/share/agenthub/configs/

# Check if AgentHub is using correct config path
cat ~/.local/share/agenthub/.env | grep CONFIG
```

**Solutions:**

#### Solution 1: Fix JSON syntax errors

```bash
# Validate JSON
python3 -m json.tool configs/mcp-servers.json

# If invalid, common issues:
# - Missing commas
# - Trailing commas (not allowed in JSON)
# - Unescaped backslashes in paths
# - Missing quotes around strings
```

#### Solution 2: Restart AgentHub to reload config

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

#### Solution 3: Verify config file path
Check `.env`:

```bash
cat ~/.local/share/agenthub/.env | grep CONFIG

# Should show:
# MCP_SERVERS_CONFIG=configs/mcp-servers.json
# ENHANCEMENT_RULES_CONFIG=configs/enhancement-rules.json
```

---

## Getting More Help

### Enable Debug Logging

Edit `.env`:

```bash
LOG_LEVEL=DEBUG
```

Restart AgentHub and check logs:

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
tail -f ~/Library/Logs/agenthub-router.log
```

---

### Collect Diagnostic Information

Run this script to gather diagnostic info:

```bash
#!/bin/bash
echo "=== AgentHub Diagnostics ==="
echo ""
echo "--- Health Check ---"
curl -s http://localhost:9090/health || echo "Health check failed"
echo ""
echo "--- MCP Servers ---"
curl -s http://localhost:9090/servers || echo "Server list failed"
echo ""
echo "--- Process Status ---"
ps aux | grep "uvicorn router.main:app"
echo ""
echo "--- Port Status ---"
lsof -i :9090
echo ""
echo "--- Recent Logs ---"
tail -20 ~/Library/Logs/agenthub-router.log
```

---

## Key Takeaways

- ✅ **First step:** Always run the Quick Diagnostic Checklist at the top of this guide
- ✅ **Health check:** `curl http://localhost:9090/health` is your best friend
- ✅ **Check logs:** `tail -f ~/Library/Logs/agenthub-router.log` shows real-time errors
- ✅ **Restart fixes most issues:** `launchctl unload/load` resolves many problems
- ✅ **Circuit breaker:** Wait 30 seconds for automatic recovery before manual intervention
- ✅ **Credentials:** All API keys go in macOS Keychain with `agenthub.*` prefix

**Next steps:**
- See [Health Checks](health-checks.md) for verification procedures
- See client-specific troubleshooting in integration guides:
  - [Claude Desktop](../03-integrations/claude-desktop.md#troubleshooting)
  - [VS Code](../03-integrations/vscode.md#troubleshooting)
  - [Raycast](../03-integrations/raycast.md#troubleshooting)

---

**Last Updated:** 2026-02-05
**Reference:** This is the single source of truth for common issues - always reference this instead of duplicating troubleshooting content.
