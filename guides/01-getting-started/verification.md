# Installation Verification Guide

**Comprehensive testing to ensure AgentHub is working correctly**

> **What you'll learn:** How to verify your installation, test all components, and troubleshoot common issues

---

## Overview

### What This Guide Covers
- Health check procedures
- MCP server testing
- Client connectivity verification
- Enhancement testing
- Common first-use issues
- Daily usage patterns

### Prerequisites
- ✅ Completed installation ([Quick Start](quick-start.md) or [Detailed Guide](detailed-installation.md))
- ✅ AgentHub running (manually or via LaunchAgent)
- ✅ At least one client configured

### Estimated Time
- Basic verification: 5 minutes
- Comprehensive testing: 15 minutes

---

## Level 1: Basic Health Checks

### Check 1: AgentHub is Running

```bash
curl http://localhost:9090/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-05T10:30:00Z",
  "version": "0.1.0"
}
```

**✅ Pass criteria:** Status is "healthy" and you get a JSON response

**❌ If it fails:**
```
curl: (7) Failed to connect to localhost port 9090: Connection refused
```

**Solution:**
1. Check if AgentHub process is running:
   ```bash
   ps aux | grep "uvicorn router.main:app"
   ```

2. If not running, start it:
   ```bash
   cd ~/.local/share/agenthub
   source .venv/bin/activate
   uvicorn router.main:app --port 9090
   ```

3. If LaunchAgent should be running:
   ```bash
   launchctl list | grep com.agenthub.router
   ```

See [Common Troubleshooting](../_shared/troubleshooting-common.md#connection-refused) for more solutions.

---

### Check 2: Dashboard Loads

**Open browser:**
```
http://localhost:9090/dashboard
```

**✅ Pass criteria:** Dashboard loads showing:
- Server list
- Activity log
- Circuit breaker status
- System metrics

**❌ If it fails:** Browser shows "This site can't be reached"

**Solution:** Same as Check 1 — ensure AgentHub is running.

---

### Check 3: LaunchAgent Auto-Start (Optional)

**If you set up LaunchAgent, verify it's loaded:**

```bash
launchctl list | grep com.agenthub.router
```

**Expected output:**
```
12345  0  com.agenthub.router
```

**What the numbers mean:**
- `12345` - Process ID (PID), proves it's running
- `0` - Exit status (0 = successful)

**✅ Pass criteria:** Service shows in list with a PID

**❌ If it fails:** No output

**Solution:**
```bash
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

## Level 2: MCP Server Verification

### Check 4: List MCP Servers

```bash
curl http://localhost:9090/servers
```

**Expected output:**
```json
{
  "servers": [
    {
      "name": "filesystem",
      "status": "running",
      "auto_start": true,
      "restart_on_failure": true
    },
    {
      "name": "fetch",
      "status": "running",
      "auto_start": true,
      "restart_on_failure": true
    }
  ]
}
```

**✅ Pass criteria:** All servers show `status: "running"`

**❌ If servers show "stopped":**

**Solution:**
```bash
# Start a specific server
curl -X POST http://localhost:9090/servers/filesystem/start

# Verify it started
curl http://localhost:9090/servers
```

---

### Check 5: Test Filesystem MCP Server

```bash
curl -X POST http://localhost:9090/mcp/filesystem/list_allowed_directories \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "list_allowed_directories",
    "params": {}
  }'
```

**Expected output:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "directories": [
      "/Users/username/Documents",
      "/Users/username/Downloads"
    ]
  }
}
```

**✅ Pass criteria:** Returns list of directories (even if empty)

**❌ If it fails:**
```json
{"error": "Server 'filesystem' not found"}
```

**Solution:**
1. Check MCP server config:
   ```bash
   cat ~/.local/share/agenthub/configs/mcp-servers.json
   ```

2. Ensure MCP packages are installed:
   ```bash
   cd ~/.local/share/agenthub/mcps
   npm install
   ```

3. Restart AgentHub

---

### Check 6: Test Fetch MCP Server

```bash
curl -X POST http://localhost:9090/mcp/fetch/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "fetch",
    "params": {"url": "https://example.com"}
  }'
```

**Expected output:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": "<!DOCTYPE html>..."
  }
}
```

**✅ Pass criteria:** Returns HTML content from example.com

**❌ If it fails:** Check firewall or network settings

---

## Level 3: Client Connectivity

### Check 7: Claude Desktop Connection

**Method 1: Ask directly**
1. Open Claude Desktop
2. Ask: "Am I connected to AgentHub?"
3. Should confirm connection

**Method 2: Check config**
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Should contain:**
```json
{
  "mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      ...
    }
  }
}
```

**Method 3: Check dashboard**
- Open `http://localhost:9090/dashboard`
- Look for recent activity from `claude-desktop` client

**✅ Pass criteria:** Any method confirms connection

**❌ If not connected:**
1. Verify config file is correct
2. Restart Claude Desktop (Cmd + Q, then reopen)
3. Check AgentHub logs for connection attempts

---

### Check 8: VS Code Connection

**Method 1: Cline sidebar**
1. Open VS Code
2. Open Cline sidebar
3. Should show "Connected to agenthub"

**Method 2: Check settings**
```bash
code ~/.vscode/settings.json
```

**Should contain:**
```json
{
  "cline.mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      ...
    }
  }
}
```

**Method 3: Test a prompt**
- Open Cline
- Ask: "What MCP servers are available?"
- Should list filesystem, fetch, etc.

**✅ Pass criteria:** Cline shows connection status

---

### Check 9: Raycast Connection

**Method 1: Test query**
1. Open Raycast (Cmd + Space)
2. Type query to AI
3. Should get response

**Method 2: Check config**
```bash
cat ~/Library/Application\ Support/com.raycast.macos/mcp_servers.json
```

**Should contain agenthub configuration**

**✅ Pass criteria:** Raycast AI responds to queries

---

## Level 4: Enhancement Testing

### Check 10: Ollama is Running

```bash
curl http://localhost:11434/api/version
```

**Expected output:**
```json
{"version":"0.1.20"}
```

**✅ Pass criteria:** Returns version number

**❌ If it fails:**
```bash
# Start Ollama
brew services start ollama

# Verify
curl http://localhost:11434/api/version
```

---

### Check 11: Models are Downloaded

```bash
ollama list
```

**Expected output:**
```
NAME                    SIZE
llama3.2:latest        2.0 GB
deepseek-r1:7b         4.1 GB
qwen2.5-coder:7b       4.7 GB
```

**✅ Pass criteria:** At least one model is listed

**❌ If no models:**
```bash
ollama pull llama3.2
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
```

---

### Check 12: Enhancement Works

```bash
curl -X POST http://localhost:9090/ollama/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: test-client" \
  -d '{
    "prompt": "List files",
    "model": "llama3.2",
    "system_prompt": "You are helpful"
  }'
```

**Expected output:**
```json
{
  "enhanced_prompt": "Please list all files...",
  "original_prompt": "List files",
  "model_used": "llama3.2"
}
```

**✅ Pass criteria:** Returns enhanced_prompt that's more detailed than original

**❌ If it fails:** Check Ollama is running and model is downloaded

---

## Level 5: End-to-End Testing

### Check 13: Full Workflow Test

**Using Claude Desktop:**

1. **Basic query:**
   ```
   What's the capital of France?
   ```
   **Expected:** Answer with Paris

2. **Context-aware query:**
   ```
   Remember I prefer TypeScript. What's the syntax for async/await?
   ```
   **Expected:** TypeScript-specific answer with async/await syntax

3. **MCP tool usage:**
   ```
   What files are in my Documents folder?
   ```
   **Expected:** Uses filesystem MCP server, lists actual files

**Using VS Code:**

1. **Code generation:**
   ```
   Create a React button component
   ```
   **Expected:** Generates actual code using Qwen3-Coder

2. **File reading:**
   ```
   Review the README.md file
   ```
   **Expected:** Uses filesystem to read actual README

**Using Raycast:**

1. **Quick query:**
   ```
   git command to undo last commit
   ```
   **Expected:** Fast, concise response (< 200 words)

**✅ Pass criteria:** All queries get appropriate responses

---

## Common First-Use Issues

### Issue 1: "Prompt not enhanced"

**Symptom:** Responses seem generic, not improved

**Check:**
```bash
# Verify enhancement is enabled in client config
# For Claude Desktop:
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep "X-Enhance"

# Should show: "X-Enhance": "true"
```

**Solution:** Ensure `X-Enhance: true` header is set in client config

---

### Issue 2: "MCP server not responding"

**Symptom:** Client shows "Server timeout" or "No response"

**Check:**
```bash
# Check circuit breaker status
curl http://localhost:9090/servers
```

**Solution:** If circuit breaker is OPEN:
```bash
# Wait 30 seconds for automatic recovery, or manually restart:
curl -X POST http://localhost:9090/servers/filesystem/stop
curl -X POST http://localhost:9090/servers/filesystem/start
```

---

### Issue 3: "Slow responses"

**Symptom:** Queries take > 5 seconds

**Check:**
```bash
# Test Ollama performance
time ollama run llama3.2 "test"
```

**Solution:** If slow:
- Use smaller model: `llama3.2:1b`
- Disable enhancement temporarily: `X-Enhance: false`
- Check system resources: `top -o cpu`

---

### Issue 4: "Authentication errors"

**Symptom:** Brave Search or other APIs fail

**Check:**
```bash
# Verify credentials are stored
security find-generic-password -s "agenthub.brave_api_key" -w
```

**Solution:** If missing:
```bash
security add-generic-password \
  -s "agenthub.brave_api_key" \
  -a "agenthub" \
  -w "YOUR_API_KEY"
```

---

## Daily Usage Patterns

### Starting Your Day

**If using LaunchAgent:**
- Nothing needed! AgentHub starts automatically when you log in
- Just open your apps and go

**If running manually:**
```bash
cd ~/.local/share/agenthub
source .venv/bin/activate
uvicorn router.main:app --port 9090
```

---

### Quick Health Check

**Before important work:**
```bash
# Quick check
curl http://localhost:9090/health

# Detailed check
curl http://localhost:9090/servers
```

---

### Viewing Logs

**Check for errors:**
```bash
# If using LaunchAgent:
tail -f ~/Library/Logs/agenthub-router.log
tail -f ~/Library/Logs/agenthub-router-error.log

# If running manually:
# Logs appear in Terminal where you started it
```

---

### Restarting AgentHub

**If using LaunchAgent:**
```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

**If running manually:**
- Press `Ctrl + C` in Terminal to stop
- Run start command again

---

## Verification Checklist

Before considering installation complete, verify:

### Basic Functionality
- [ ] Health endpoint responds
- [ ] Dashboard loads
- [ ] LaunchAgent is loaded (if configured)

### MCP Servers
- [ ] All configured servers show "running" status
- [ ] Filesystem server can list directories
- [ ] Fetch server can retrieve web content

### Client Connectivity
- [ ] At least one client (Claude/VS Code/Raycast) is connected
- [ ] Client config files are correctly formatted
- [ ] Dashboard shows client activity

### Enhancement
- [ ] Ollama is running
- [ ] Required models are downloaded
- [ ] Enhancement endpoint works

### End-to-End
- [ ] Can ask questions and get responses
- [ ] MCP tools work from clients
- [ ] Enhancement improves prompts (if enabled)
- [ ] No errors in logs

### All checks pass? ✅ **Installation verified!**

---

## Performance Benchmarks

### Expected Response Times

| Operation | Expected Time | Acceptable | Slow |
|-----------|---------------|------------|------|
| Health check | < 50ms | < 200ms | > 200ms |
| MCP server query | < 500ms | < 2s | > 2s |
| Enhancement | < 2s | < 5s | > 5s |
| Client query | < 3s | < 10s | > 10s |

**If consistently slow:** See [Common Troubleshooting](../_shared/troubleshooting-common.md#slow-responses)

---

## Next Steps

### You're Ready!
- [Workflows](../04-workflows/) - Learn practical usage patterns
- [Core Setup](../02-core-setup/) - Optional enhancements (Keychain, Docker)
- [Integrations](../03-integrations/) - Connect more clients

### Troubleshooting Resources
- [Common Issues](../_shared/troubleshooting-common.md)
- [Health Checks](../_shared/health-checks.md)
- [Terminology](../_shared/terminology.md)

---

**Last Updated:** 2026-02-05
**Audience:** All users
**Time:** 5-15 minutes
**Difficulty:** Beginner
