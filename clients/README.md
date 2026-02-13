# Client Configurations

This folder contains client-specific configuration files for connecting various applications to PromptHub.

## Structure

```
clients/
├── claude/          # Claude Desktop configurations
├── raycast/         # Raycast script and MCP configs
└── vscode/          # VS Code workspace and MCP settings
```

## Quick Start

Each client folder contains:
- **Example configurations** - Ready-to-use templates
- **README.md** - Client-specific setup instructions
- **Best practices** - Recommended settings and workflows

## Supported Clients

### Claude Desktop
- **Transport:** stdio (Node.js MCP server)
- **Configuration:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Enhancement Model:** DeepSeek-R1 (comprehensive reasoning)
- [Setup Guide](claude/README.md)

### VS Code (Claude Code / Cline)
- **Transport:** HTTP
- **Configuration:** Workspace `.vscode/settings.json`
- **Enhancement Model:** Qwen3-Coder (code-first)
- [Setup Guide](vscode/README.md)

### Raycast
- **Transport:** HTTP (via curl scripts)
- **Configuration:** Custom script commands
- **Enhancement Model:** DeepSeek-R1 (action-oriented)
- [Setup Guide](raycast/README.md)

## Architecture

All clients connect to PromptHub's HTTP router at `http://localhost:9090`:

```
┌─────────────────┐
│ Claude Desktop  │ ──stdio──> Node MCP Bridge ──┐
└─────────────────┘                              │
                                                 ▼
┌─────────────────┐                      ┌──────────────┐
│ VS Code         │ ──HTTP───────────────> PromptHub     │
└─────────────────┘                      │ Router       │
                                         │ :9090        │
┌─────────────────┐                      └──────────────┘
│ Raycast         │ ──HTTP (curl)────────┘      │
└─────────────────┘                             │
                                                ▼
                                         7 MCP Servers
                                         (context7, fetch, etc.)
```

## Client-Specific Features

### Custom Instructions (Claude Desktop)
Recommended tool usage policy for automatic, safe tool use:
```
Tool Usage Policy:
- Use MCP tools automatically when clearly useful
- Mention when accessing tools
- Request permission before modifying system files
```

### Tasks Integration (VS Code)
Pre-configured tasks for common operations:
- Health checks
- Server management
- Documentation generation

### Script Commands (Raycast)
Quick-access scripts for:
- MCP queries
- Server status
- Common workflows

## PromptHub Configuration

Client-independent PromptHub settings are in the parent `configs/` folder:

- `enhancement-rules.json` - Per-client prompt enhancement
- `mcp-servers.json` - MCP server registry
- `mcp-servers-keyring.json.example` - Credential management

## Choosing a Configuration

**Use the unified MCP bridge** (Claude Desktop only):
- ✅ Simplest setup (single MCP server entry)
- ✅ All 7 servers accessible
- ✅ Native JSON-RPC 2.0 protocol
- ✅ Recommended for most users

**Use direct HTTP** (VS Code, Raycast):
- ✅ Lower latency
- ✅ Better for programmatic access
- ✅ RESTful API integration

## Troubleshooting

### Connection Issues
1. Verify PromptHub is running: `curl http://localhost:9090/health`
2. Check client logs for errors
3. Confirm configuration paths are correct

### Tool Discovery Issues
1. Ensure server is running: `curl http://localhost:9090/servers`
2. Test direct endpoint: `curl http://localhost:9090/mcp/context7/tools/call`
3. Check client headers include `X-Client-Name`

### Enhancement Not Working
1. Verify Ollama is running: `ollama list`
2. Check enhancement rules: `configs/enhancement-rules.json`
3. Confirm client name matches configuration

## Documentation

Full integration guides are in the Obsidian vault at `~/Vault/PromptHub/Integrations/`.
