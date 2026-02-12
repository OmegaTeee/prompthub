# MCP Servers Directory

This directory contains all local MCP (Model Context Protocol) servers.

## Structure

```
mcps/
├── package.json              # npm dependencies for Node.js MCP servers
├── node_modules/             # Installed npm packages (6 servers)
├── obsidian-mcp-tools/       # Obsidian standalone binary
│   ├── bin/mcp-server        # ARM64 compiled executable
│   ├── manifest.json         # Version info
│   ├── README.md             # Server documentation
│   └── PYTHON-MCP-EXAMPLE.md # How to add Python MCP servers
└── README.md                 # This file
```

## Active MCP Servers (7 total)

### Node.js Packages (6 servers)
Installed via `npm install` in this directory:

1. **context7** - `@upstash/context7-mcp`
   - Documentation fetching from libraries
   - Auto-start: Yes

2. **desktop-commander** - `@wonderwhy-er/desktop-commander`
   - File operations and terminal commands
   - Auto-start: Yes

3. **sequential-thinking** - `@modelcontextprotocol/server-sequential-thinking`
   - Step-by-step reasoning and planning
   - Auto-start: Yes

4. **memory** - `@modelcontextprotocol/server-memory`
   - Cross-session context persistence
   - Auto-start: No

5. **deepseek-reasoner** - `deepseek-reasoner-mcp`
   - Local reasoning without API costs
   - Auto-start: No

6. **fetch** - `mcp-fetch`
   - HTTP fetch, GraphQL, WebSocket, browser automation
   - Auto-start: No

### Standalone Binary (1 server)

1. **obsidian** - `obsidian-mcp-tools`
   - Semantic search, templates, file management for Obsidian vault
   - Location: `obsidian-mcp-tools/bin/mcp-server`
   - Auto-start: Yes
   - Requires: API key in macOS Keychain

## Configuration

All servers are configured in [`../configs/mcp-servers.json`](../configs/mcp-servers.json).

Servers requiring API keys use wrapper scripts in [`../scripts/`](../scripts/) that load credentials from macOS Keychain.

## Adding New MCP Servers

### For npm Packages

```bash
cd mcps
npm install <package-name>
```

Then add to `configs/mcp-servers.json`:

```json
{
  "<server-name>": {
    "package": "<package-name>",
    "transport": "stdio",
    "command": "node",
    "args": ["./mcps/node_modules/<package-name>/dist/index.js"],
    "auto_start": false
  }
}
```

### For Standalone Binaries

```bash
mkdir -p mcps/<mcp-name>/bin
cp /path/to/binary mcps/<mcp-name>/bin/
chmod +x mcps/<mcp-name>/bin/<binary>
```

Create wrapper script in `scripts/` if API keys needed. See [`scripts/obsidian-mcp-tools.sh`](../scripts/obsidian-mcp-tools.sh) for pattern.

### For Python Packages

See [`obsidian-mcp-tools/PYTHON-MCP-EXAMPLE.md`](obsidian-mcp-tools/PYTHON-MCP-EXAMPLE.md) for complete guide.

Example configurations available in [`../configs/mcp-servers.json.examples`](../configs/mcp-servers.json.examples).

## Validation

Run the validation script to verify all servers are installed:

```bash
../scripts/validate-mcp-servers.sh
```

This checks:
- ✅ Node.js and npx availability
- ✅ All npm package files exist
- ✅ JavaScript syntax validation
- ✅ Standalone binaries
- ✅ Python packages (if any)

## Upgrading Servers

### npm Packages

```bash
cd mcps
npm update <package-name>
# or
npm update  # update all
```

### Obsidian Binary
1. Update plugin in Obsidian
2. Copy new binary:

```bash
cp ~/Obsidian/.obsidian/plugins/mcp-tools/bin/mcp-server \
   obsidian-mcp-tools/bin/
```

## References

- [Model Context Protocol](https://modelcontextprotocol.io) - Official MCP specification
- [MCP Servers Registry](https://github.com/modelcontextprotocol/servers) - Official MCP servers
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) - Community list
