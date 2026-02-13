# Client Scripts

Scripts for generating client configurations and bridging MCP protocols.

## Scripts

### `generate-claude-config.py`
Generates Claude Desktop MCP configuration from PromptHub MCP server registry.

**Purpose:** Automates creation of `claude_desktop_config.json` from `configs/mcp-servers.json`.

**Usage:**

```bash
python3 clients/generate-claude-config.py

# Output written to:
# ~/Library/Application Support/Claude/claude_desktop_config.json
```

**Features:**
- Reads from `configs/mcp-servers.json`
- Generates stdio-based MCP server entries
- Handles API key wrapper scripts
- Creates backup of existing config
- Validates Node.js MCP server paths

**Dependencies:**
- Python 3.8+
- `configs/mcp-servers.json` must exist

**Example output:**

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "obsidian": {
      "command": "/Users/user/.local/share/prompthub/scripts/mcps/obsidian-mcp-tools.sh"
    }
  }
}
```

### `mcp-stdio-bridge.sh`
Bridges HTTP MCP requests to stdio-based MCP servers (legacy approach).

**Purpose:** Allows Claude Desktop to communicate with PromptHub via stdio protocol.

**Usage:**

```bash
# Called by Claude Desktop config
node /path/to/mcp-stdio-bridge.sh

# Or test manually
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | ./mcp-stdio-bridge.sh
```

**Features:**
- Translates stdio JSON-RPC to HTTP requests
- Forwards to PromptHub at `http://localhost:9090`
- Handles error responses
- Supports all MCP methods (tools/list, tools/call, etc.)

**Note:** The **unified MCP bridge** (`mcps/prompthub-bridge.js`) is now the recommended approach. This script is kept for backwards compatibility.

**Dependencies:**
- PromptHub running on `localhost:9090`
- `curl` available in PATH
- `jq` for JSON processing

## When to Use These Scripts

### Use `generate-claude-config.py` when:
- ✅ You want individual stdio connections to each MCP server
- ✅ You need granular control over which servers Claude Desktop sees
- ✅ You're debugging specific MCP server issues
- ✅ You want to bypass PromptHub's HTTP layer

### Use the unified bridge instead when:
- ✅ You want all MCP servers in one connection (recommended)
- ✅ You want prompt enhancement via PromptHub
- ✅ You want circuit breaker protection
- ✅ You want audit logging of MCP requests

See [Claude setup](claude/) for unified bridge setup.

## Comparison: Generated Config vs Unified Bridge

**Generated Config (Individual Servers):**

```json
{
  "mcpServers": {
    "context7": { "command": "npx", "args": [...] },
    "fetch": { "command": "node", "args": [...] },
    "obsidian": { "command": "./scripts/mcps/obsidian-mcp-tools.sh" },
    ...
  }
}
```

- 7+ separate MCP connections
- No prompt enhancement
- No audit logging
- Direct server access

**Unified Bridge (Single Connection):**

```json
{
  "mcpServers": {
    "prompthub": {
      "command": "node",
      "args": ["~/.local/share/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "PROMPTHUB_URL": "http://localhost:9090",
        "CLIENT_NAME": "claude-desktop"
      }
    }
  }
}
```

- 1 MCP connection (aggregates all 7 servers)
- Prompt enhancement with DeepSeek-R1
- Full audit logging
- Circuit breaker protection
- Tool names prefixed: `context7_query-docs`

## Migration Guide

### From Individual Servers → Unified Bridge

1. **Backup current config:**

   ```bash
   cp ~/Library/Application\ Support/Claude/claude_desktop_config.json \
      ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup
   ```

2. **Use setup script:**

   ```bash
   clients/claude/setup-claude.sh
   ```

3. **Restart Claude Desktop:**

   ```bash
   osascript -e 'quit app "Claude"' && open -a "Claude"
   ```

4. **Verify:**
   - Look for `🔌 prompthub` badge at bottom
   - Ask: "What MCP tools are available?"
   - Should see tools like `context7_query-docs`, `fetch_fetch`, etc.

### From Unified Bridge → Individual Servers

1. **Generate new config:**

   ```bash
   python3 clients/generate-claude-config.py
   ```

2. **Restart Claude Desktop:**

   ```bash
   osascript -e 'quit app "Claude"' && open -a "Claude"
   ```

3. **Verify:**
   - Look for multiple MCP badges
   - Should see `context7`, `fetch`, `obsidian`, etc. separately

## Troubleshooting

### Config Generation Issues

**Problem:** `generate-claude-config.py` fails with "File not found"

**Solution:**

```bash
# Ensure MCP server registry exists
ls -la configs/mcp-servers.json

# Run from PromptHub root directory
cd ~/.local/share/prompthub
python3 clients/generate-claude-config.py
```

**Problem:** Generated config has missing servers

**Solution:**

```bash
# Validate MCP servers are configured
scripts/router/validate-mcp-servers.sh

# Check for errors in mcp-servers.json
cat configs/mcp-servers.json | jq .
```

### Bridge Issues

**Problem:** `mcp-stdio-bridge.sh` returns "Connection refused"

**Solution:**

```bash
# Ensure PromptHub is running
curl http://localhost:9090/health

# Start PromptHub if needed
launchctl start com.prompthub.router
```

**Problem:** Responses are malformed

**Solution:**

```bash
# Check jq is installed
which jq
brew install jq

# Test bridge manually
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | clients/mcp-stdio-bridge.sh
```

## Development

### Testing Config Generation

```bash
# Dry run (print to stdout)
python3 clients/generate-claude-config.py --dry-run

# Validate output
python3 clients/generate-claude-config.py --dry-run | jq .
```

### Testing Bridge

```bash
# Test tools/list
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | clients/mcp-stdio-bridge.sh | jq .

# Test tools/call
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"fetch_fetch","arguments":{"url":"https://example.com"}},"id":2}' | \
  clients/mcp-stdio-bridge.sh | jq .
```

## Related Documentation

- [Claude Desktop Integration Guide](../guides/claude-desktop-integration.md)
- [Unified MCP Bridge](claude/README.md)
- [Testing Integrations](../guides/testing-integrations.md)
