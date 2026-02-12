# AgentHub Health Checks

**Purpose:** Centralized reference for verifying AgentHub is running correctly.

> **What you'll learn:** How to check if AgentHub is healthy, diagnose common issues, and verify MCP server connectivity.

---

## Quick Health Check

### Basic Test

```bash
curl http://localhost:9090/health
```

**Expected output:**

```json
{"status":"healthy","timestamp":"2026-02-05T10:30:00Z","version":"0.1.0"}
```

**What it means:**
- ✅ AgentHub is running
- ✅ HTTP server is responding
- ✅ Port 9090 is accessible

---

## Detailed Health Verification

### 1. Check AgentHub Process

**macOS/Linux:**

```bash
ps aux | grep "uvicorn router.main:app"
```

**Expected output:**

```
user    12345  0.5  1.2  uvicorn router.main:app --host 0.0.0.0 --port 9090
```

**What it means:**
- ✅ AgentHub process is running
- Shows PID (12345 in example)
- Shows resource usage (CPU 0.5%, Memory 1.2%)

---

### 2. Check Port Availability

```bash
lsof -i :9090
```

**Expected output:**

```
COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
Python    12345 user   6u  IPv4 0xabcd      0t0  TCP *:9090 (LISTEN)
```

**What it means:**
- ✅ Port 9090 is open and listening
- Shows which process is using the port
- Confirms AgentHub is bound to the port

**If port is in use by another process:**

```bash
# Find what's using port 9090
lsof -i :9090

# Kill the conflicting process (use with caution)
kill -9 <PID>
```

---

### 3. Check LaunchAgent Status (macOS)

```bash
launchctl list | grep com.agenthub.router
```

**Expected output:**

```
12345  0  com.agenthub.router
```

**What it means:**
- ✅ LaunchAgent is loaded
- First number (12345) is PID (0 if not running)
- Second number (0) is exit status (0 = success)

**Check LaunchAgent logs:**

```bash
tail -f ~/Library/Logs/agenthub-router.log
```

---

### 4. Verify Dashboard Access

**Open in browser:**

```
http://localhost:9090/dashboard
```

**What you should see:**
- ✅ AgentHub monitoring dashboard
- ✅ List of MCP servers
- ✅ Recent activity log
- ✅ Circuit breaker status

**If dashboard doesn't load:**
- Check browser console for errors
- Verify AgentHub is running (`curl http://localhost:9090/health`)
- Check firewall settings

---

## MCP Server Health Checks

### List All MCP Servers

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

**What it means:**
- ✅ All configured MCP servers are listed
- `status: "running"` = server is operational
- `status: "stopped"` = server is not running

---

### Start a Specific MCP Server

```bash
curl -X POST http://localhost:9090/servers/filesystem/start
```

**Expected output:**

```json
{"status":"success","message":"Server 'filesystem' started"}
```

---

### Stop a Specific MCP Server

```bash
curl -X POST http://localhost:9090/servers/filesystem/stop
```

**Expected output:**

```json
{"status":"success","message":"Server 'filesystem' stopped"}
```

---

## Testing MCP Connectivity

### Test Filesystem MCP Server

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
    "directories": ["/Users/username/Documents", "/Users/username/Downloads"]
  }
}
```

**What it means:**
- ✅ MCP server is responding
- ✅ JSON-RPC communication works
- ✅ Server returns expected data

---

### Test Fetch MCP Server

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

---

## Enhancement Testing

### Test Ollama Connectivity

```bash
curl http://localhost:11434/api/version
```

**Expected output:**

```json
{"version":"0.1.20"}
```

**What it means:**
- ✅ Ollama is running
- ✅ Port 11434 is accessible
- Shows Ollama version

---

### Test Prompt Enhancement

```bash
curl -X POST http://localhost:9090/ollama/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: test-client" \
  -d '{
    "prompt": "List files in directory",
    "model": "llama3.2",
    "system_prompt": "You are a helpful assistant"
  }'
```

**Expected output:**

```json
{
  "enhanced_prompt": "Please list all files in the current directory...",
  "original_prompt": "List files in directory",
  "model_used": "llama3.2"
}
```

**What it means:**
- ✅ Enhancement is working
- ✅ Ollama is responding
- ✅ Prompt was improved

---

## Circuit Breaker Status

### Check Circuit Breaker State

```bash
curl http://localhost:9090/dashboard | grep -i "circuit"
```

**Or view in dashboard:**

```
http://localhost:9090/dashboard
```

**Possible states:**
- ✅ **CLOSED** - Normal operation
- ⚠️ **OPEN** - Server failing, requests blocked
- 🔄 **HALF_OPEN** - Testing recovery

**What each state means:**
- **CLOSED:** All requests go through normally
- **OPEN:** Requests are rejected to prevent cascading failures (after 3+ consecutive failures)
- **HALF_OPEN:** Testing if server has recovered (after 30-second timeout)

---

## Common Health Check Failures

### Issue: "Connection refused"

```bash
curl http://localhost:9090/health
# curl: (7) Failed to connect to localhost port 9090: Connection refused
```

**Diagnosis:**
- ❌ AgentHub is not running

**Solutions:**
1. Start AgentHub manually:

   ```bash
   cd ~/.local/share/agenthub
   uvicorn router.main:app --host 0.0.0.0 --port 9090
   ```

2. Check LaunchAgent status:

   ```bash
   launchctl list | grep com.agenthub.router
   ```

3. Restart LaunchAgent:

   ```bash
   launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
   launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
   ```

---

### Issue: "Empty response"

```bash
curl http://localhost:9090/health
# curl: (52) Empty reply from server
```

**Diagnosis:**
- ⚠️ AgentHub started but crashed
- ⚠️ Python dependencies missing

**Solutions:**
1. Check logs:

   ```bash
   tail -f ~/Library/Logs/agenthub-router.log
   ```

2. Reinstall dependencies:

   ```bash
   cd ~/.local/share/agenthub
   pip install -r requirements.txt
   ```

3. Test manually:

   ```bash
   cd ~/.local/share/agenthub
   uvicorn router.main:app --reload --port 9090
   ```

---

### Issue: "MCP server not found"

```bash
curl http://localhost:9090/mcp/filesystem/list_allowed_directories
# {"error": "Server 'filesystem' not found"}
```

**Diagnosis:**
- ❌ MCP server not configured
- ❌ MCP server failed to start

**Solutions:**
1. Check server list:

   ```bash
   curl http://localhost:9090/servers
   ```

2. Verify config file:

   ```bash
   cat ~/.local/share/agenthub/configs/mcp-servers.json
   ```

3. Start server manually:

   ```bash
   curl -X POST http://localhost:9090/servers/filesystem/start
   ```

---

### Issue: "Circuit breaker OPEN"

```bash
curl http://localhost:9090/mcp/filesystem/list_allowed_directories
# {"error": "Circuit breaker OPEN for server 'filesystem'"}
```

**Diagnosis:**
- ⚠️ MCP server has failed 3+ times
- ⚠️ Circuit breaker protecting against cascading failures

**Solutions:**
1. Wait 30 seconds for automatic recovery attempt
2. Check server logs for root cause:

   ```bash
   tail -f ~/Library/Logs/agenthub-router.log
   ```

3. Restart MCP server:

   ```bash
   curl -X POST http://localhost:9090/servers/filesystem/stop
   curl -X POST http://localhost:9090/servers/filesystem/start
   ```

---

## Performance Monitoring

### Check Response Times

```bash
time curl http://localhost:9090/health
```

**Expected output:**

```
{"status":"healthy"}

real    0m0.015s  # < 50ms is good
user    0m0.003s
sys     0m0.005s
```

**What it means:**
- ✅ < 50ms: Excellent performance
- ⚠️ 50-200ms: Acceptable performance
- ❌ > 200ms: Performance issue (check logs)

---

### Check Memory Usage

```bash
ps aux | grep "uvicorn router.main:app" | awk '{print $4, $6}'
```

**Expected output:**

```
1.2 204800  # 1.2% CPU, ~200MB memory
```

**What it means:**
- ✅ < 500MB: Normal memory usage
- ⚠️ 500MB-1GB: High usage (monitor for leaks)
- ❌ > 1GB: Memory leak (restart recommended)

---

## Automated Health Monitoring

### Create a Health Check Script

```bash
#!/bin/bash
# save as: ~/bin/check-agenthub.sh

HEALTH_URL="http://localhost:9090/health"
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null $HEALTH_URL)

if [ "$RESPONSE" -eq 200 ]; then
    echo "✅ AgentHub is healthy"
    exit 0
else
    echo "❌ AgentHub is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

**Make it executable:**

```bash
chmod +x ~/bin/check-agenthub.sh
```

**Run it:**

```bash
~/bin/check-agenthub.sh
```

---

### Schedule Regular Health Checks (macOS)

Create a LaunchAgent for monitoring:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agenthub.healthcheck</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/YOUR_USERNAME/bin/check-agenthub.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer> <!-- Check every 5 minutes -->
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/agenthub-healthcheck.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/agenthub-healthcheck-error.log</string>
</dict>
</plist>
```

---

## Key Takeaways

- ✅ **Quick check:** `curl http://localhost:9090/health`
- ✅ **Dashboard:** `http://localhost:9090/dashboard` for visual monitoring
- ✅ **Process check:** `ps aux | grep uvicorn` to verify AgentHub is running
- ✅ **Port check:** `lsof -i :9090` to confirm port binding
- ✅ **MCP servers:** `curl http://localhost:9090/servers` to list server status
- ✅ **Circuit breaker:** Check dashboard for server health status

**Next steps:**
- See [Common Troubleshooting](troubleshooting-common.md) for detailed issue resolution
- See [Integration Tests](../05-testing/integration-tests.md) for comprehensive testing
- See [Dashboard Usage](../05-testing/health-monitoring.md) for monitoring guide (coming soon)

---

**Last Updated:** 2026-02-05
**Reference:** This guide is the single source of truth for health checks - always reference this instead of duplicating health check commands.
