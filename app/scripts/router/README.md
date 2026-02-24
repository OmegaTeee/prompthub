# Router Scripts

Manage PromptHub MCP servers.

## Scripts

### `restart_mcp_servers.py`

Restart and verify MCP servers via the router API. Fetches the server list dynamically from `/servers`.

```bash
python3 scripts/router/restart_mcp_servers.py           # Restart all auto_start servers
python3 scripts/router/restart_mcp_servers.py --all     # Restart all servers including stopped
python3 scripts/router/restart_mcp_servers.py obsidian  # Restart specific server
```

Phases:
1. Stop/start each target server via HTTP API
2. Wait for initialization
3. Test `tools/list` on each server and report tool counts

Requires the router running on `localhost:9090`.

### `validate-mcp-servers.sh`

Check that MCP server binaries exist on disk. Parses `configs/mcp-servers.json` dynamically.

```bash
scripts/router/validate-mcp-servers.sh
```

For each configured server, resolves the command (or first arg for `node` commands) and checks file existence or PATH lookup. Reports found/missing counts.
