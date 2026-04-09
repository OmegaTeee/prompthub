# Claude Desktop

Bridge client using `mcpServers` format. Merge install (config includes `globalShortcut` and other preferences).

## Config path

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## Quick setup

```bash
./clients/claude/desktop-setup.sh
```

The setup script links PromptHub's tracked config into Claude Desktop while
keeping the repo as the source of truth.

## Files in this directory

- `mcp.json` — Bridge config (source of truth, symlinked to app path)
- `bridge.log` — Symlink to Claude's live MCP bridge log

## External references

- [Claude Desktop MCP docs](https://modelcontextprotocol.io/quickstart/user)
- [Claude Desktop config format](https://docs.anthropic.com/en/docs/claude-desktop/mcp)
