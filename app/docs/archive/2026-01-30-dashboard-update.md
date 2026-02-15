# Dashboard Update - Server Control Buttons

## Changes Made

### 1. Enabled Auto-Start for deepseek-reasoner
- Updated [configs/mcp-servers.json](configs/mcp-servers.json:57) to set `auto_start: true` for deepseek-reasoner
- Server now starts automatically with the router

### 2. Added Start/Stop/Restart Buttons to Dashboard
Added server control buttons to the dashboard health panel:
- **Start** button (green) - Shows when server is stopped
- **Stop** button (yellow) - Shows when server is running
- **Restart** button (grey) - Shows when server is running

#### Files Modified:
- [router/main.py](router/main.py) - Added `_start_server()` and `_stop_server()` helper functions
- [router/dashboard/router.py](router/dashboard/router.py) - Added `/actions/start/{server}` and `/actions/stop/{server}` endpoints
- [templates/dashboard.html](templates/dashboard.html) - Added button CSS styles (btn-sm, btn-warning, btn-secondary)
- [templates/partials/health.html](templates/partials/health.html) - Added server control buttons to each server status item

### 3. Server Status Summary

Current auto-start servers (5):
- ✅ context7 (PID 52431)
- ✅ desktop-commander (PID 52444)
- ✅ sequential-thinking (PID 52469)
- ✅ **deepseek-reasoner** (PID 52471) - **NEW AUTO-START**
- ✅ obsidian (PID 52472) - Using keyring credentials

Manual-start servers (2):
- ⏸️ memory - Start/stop via dashboard buttons
- ⏸️ fetch - Start/stop via dashboard buttons

## How to Use

1. **View Dashboard**: http://localhost:9090/dashboard
2. **Start a stopped server**: Click the green "Start" button
3. **Stop a running server**: Click the yellow "Stop" button
4. **Restart a server**: Click the grey "Restart" button

The dashboard auto-refreshes every 5 seconds, or buttons trigger an immediate refresh after action.

## Verification

```bash
# Check router status
curl http://localhost:9090/health | jq '.servers'

# View logs
tail -f /tmp/mcp-router.err | grep -E "keyring|Starting server"
```

All changes verified working:
- ✅ deepseek-reasoner auto-starts on router boot
- ✅ Obsidian keyring integration still working
- ✅ Dashboard buttons successfully start/stop servers
- ✅ Router remains stable with KeepAlive enabled
