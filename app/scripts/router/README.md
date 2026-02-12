# Router Management Scripts

Scripts for managing PromptHub router and MCP servers.

## Scripts

### `restart-mcp-servers.py`
Restarts all or specific MCP servers via PromptHub API.

**Purpose:** Gracefully restart MCP servers without restarting the entire router.

**Usage:**
```bash
# Restart all servers
python3 scripts/router/restart-mcp-servers.py

# Restart specific server
python3 scripts/router/restart-mcp-servers.py context7

# Restart multiple servers
python3 scripts/router/restart-mcp-servers.py context7 fetch obsidian

# Check status first
python3 scripts/router/restart-mcp-servers.py --status

# Force restart (kill and restart)
python3 scripts/router/restart-mcp-servers.py --force
```

**Features:**
- Lists all configured MCP servers
- Shows current status (running/stopped/failed)
- Graceful shutdown with timeout
- Automatic restart after shutdown
- Force kill option for hung processes
- Verifies restart success

**API Endpoints Used:**
- `GET /servers` - List all servers
- `POST /servers/{name}/stop` - Stop server
- `POST /servers/{name}/start` - Start server
- `POST /servers/{name}/restart` - Restart server

**Example output:**
```
🔄 Restarting MCP Servers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Current Status:
  ✓ context7           running   (pid: 12345)
  ✓ fetch              running   (pid: 12346)
  ✗ deepseek-reasoner  stopped

🔄 Restarting context7...
  • Stopping server... done (2.1s)
  • Starting server... done (1.3s)
  ✓ context7 restarted successfully

🔄 Restarting fetch...
  • Stopping server... done (1.8s)
  • Starting server... done (1.1s)
  ✓ fetch restarted successfully

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 2/2 servers restarted successfully
```

**Dependencies:**
- Python 3.8+
- `requests` library
- PromptHub running on `localhost:9090`

### `validate-mcp-servers.sh`
Validates all configured MCP servers are correctly installed and configured.

**Purpose:** Pre-flight check to ensure MCP servers are ready to run.

**Usage:**
```bash
# Validate all servers
scripts/router/validate-mcp-servers.sh

# Verbose output
scripts/router/validate-mcp-servers.sh -v

# Check single server
scripts/router/validate-mcp-servers.sh context7

# Fix issues automatically (if possible)
scripts/router/validate-mcp-servers.sh --fix
```

**Checks performed:**
- ✓ Node.js and npx are installed
- ✓ Python and pip are available
- ✓ MCP server files exist at expected paths
- ✓ JavaScript files have valid syntax
- ✓ Python MCP servers are installed in venv
- ✓ Required dependencies are available
- ✓ API key wrapper scripts are executable
- ✓ Keychain entries exist for wrapped servers

**Example output:**
```
🔍 Validating MCP Server Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Node.js: v20.10.0
✓ npx: available
✓ Python: 3.11.6
✓ pip: 23.3.1

Checking context7...
  ✓ NPM package: @upstash/context7-mcp
  ✓ Installation: verified
  ✓ Syntax: valid

Checking obsidian...
  ✓ Wrapper script: scripts/mcps/obsidian-mcp-tools.sh
  ✓ Executable: yes
  ✓ Keychain entry: obsidian_api_key found
  ✓ Binary: mcps/obsidian-mcp-tools/bin/mcp-server

Checking desktop-commander...
  ✓ NPM package: @wonderwhy-er/desktop-commander
  ✓ Installation: verified
  ✓ Syntax: valid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All 7 MCP servers validated successfully
```

**Exit codes:**
- `0` - All servers valid
- `1` - Validation errors found
- `2` - Critical dependency missing (Node.js/Python)

**Dependencies:**
- `bash` 4.0+
- `jq` for JSON parsing
- `node` for syntax checking
- `security` (macOS) for Keychain validation

## Common Operations

### Check Server Health

```bash
# Quick status check
curl http://localhost:9090/servers | jq '.[] | {name, status}'

# Detailed health check
for server in context7 fetch obsidian; do
  echo "=== $server ==="
  curl -s "http://localhost:9090/servers/$server" | jq .
done
```

### Restart Hung Server

```bash
# Graceful restart
python3 scripts/router/restart-mcp-servers.py obsidian

# Force restart if hung
python3 scripts/router/restart-mcp-servers.py --force obsidian
```

### Mass Restart

```bash
# Restart all servers
python3 scripts/router/restart-mcp-servers.py

# Or use PromptHub API directly
curl -X POST http://localhost:9090/servers/restart-all
```

### Validate Before Deploying

```bash
# Validate configuration
scripts/router/validate-mcp-servers.sh

# Fix common issues
scripts/router/validate-mcp-servers.sh --fix

# Start PromptHub after validation
launchctl start com.prompthub.router
```

## Troubleshooting

### Server Won't Start

**Problem:** Server fails to start after restart

**Diagnosis:**
```bash
# Check server logs
tail -f ~/.local/share/prompthub/logs/router.log | grep -i "error\|fail"

# Validate configuration
scripts/router/validate-mcp-servers.sh obsidian

# Check if port is in use
lsof -i :9090
```

**Solutions:**
```bash
# Fix permissions
chmod +x scripts/mcps/obsidian-mcp-tools.sh

# Reinstall dependencies
cd mcps && npm install

# Check Keychain for API keys
security find-generic-password -a $USER -s obsidian_api_key -w
```

### Validation Failures

**Problem:** `validate-mcp-servers.sh` reports errors

**Common issues:**

1. **Missing Node.js packages:**
   ```bash
   cd ~/.local/share/prompthub/mcps
   npm install
   ```

2. **Keychain entry missing:**
   ```bash
   security add-generic-password -a $USER -s obsidian_api_key -w YOUR_KEY
   ```

3. **Wrapper script not executable:**
   ```bash
   chmod +x scripts/mcps/*.sh
   ```

4. **Python venv not activated:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

### Restart Timeout

**Problem:** Restart script hangs or times out

**Solution:**
```bash
# Use force flag
python3 scripts/router/restart-mcp-servers.py --force

# Manually kill hung process
ps aux | grep mcp-server
kill -9 <pid>

# Restart PromptHub router
launchctl stop com.prompthub.router
launchctl start com.prompthub.router
```

## Integration with PromptHub

These scripts work with PromptHub's MCP server lifecycle management:

```python
# router/servers/lifecycle.py
async def restart_server(server_name: str):
    """
    Restart MCP server gracefully.
    Called by restart-mcp-servers.py via HTTP API.
    """
    await stop_server(server_name)
    await asyncio.sleep(2)  # Grace period
    await start_server(server_name)
```

### Circuit Breaker Integration

When a server fails repeatedly, PromptHub's circuit breaker opens:
- **CLOSED** → **OPEN** (3 failures in 30s)
- **OPEN** → **HALF_OPEN** (after 30s cooldown)
- **HALF_OPEN** → **CLOSED** (1 success)

Restart scripts can force circuit breaker reset:
```bash
python3 scripts/router/restart-mcp-servers.py --reset-circuit-breaker context7
```

## Automated Maintenance

### Cron Jobs

Add to crontab for automated maintenance:

```cron
# Validate MCP servers every 6 hours
0 */6 * * * /Users/user/.local/share/prompthub/scripts/router/validate-mcp-servers.sh

# Restart hung servers daily at 3 AM
0 3 * * * /usr/bin/python3 /Users/user/.local/share/prompthub/scripts/router/restart-mcp-servers.py --force
```

### LaunchAgent

Use macOS LaunchAgent for automated restarts:

```xml
<!-- ~/Library/LaunchAgents/com.prompthub.mcp-monitor.plist -->
<dict>
  <key>Label</key>
  <string>com.prompthub.mcp-monitor</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/user/.local/share/prompthub/scripts/router/restart-mcp-servers.py</string>
    <string>--check-only</string>
  </array>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>RunAtLoad</key>
  <true/>
</dict>
```

## Development

### Testing Restart Logic

```python
# test_restart.py
import requests

def test_restart_server():
    # Stop server
    r = requests.post("http://localhost:9090/servers/context7/stop")
    assert r.status_code == 200

    # Verify stopped
    r = requests.get("http://localhost:9090/servers/context7")
    assert r.json()["status"] == "stopped"

    # Start server
    r = requests.post("http://localhost:9090/servers/context7/start")
    assert r.status_code == 200

    # Verify running
    r = requests.get("http://localhost:9090/servers/context7")
    assert r.json()["status"] == "running"
```

### Adding New Validation Checks

Edit `validate-mcp-servers.sh` to add custom checks:

```bash
# Check custom dependency
check_custom_dependency() {
  local server_name=$1

  if [[ ! -f "custom/path/${server_name}.config" ]]; then
    log_error "${server_name}: Missing custom config"
    return 1
  fi

  log_success "${server_name}: Custom config found"
  return 0
}
```

## Related Documentation

- [MCP Server Configuration](../../configs/mcp-servers.json)
- [Router Architecture](../../docs/architecture.md)
- [Circuit Breaker](../../router/resilience/circuit_breaker.py)
- [Server Lifecycle](../../router/servers/lifecycle.py)
