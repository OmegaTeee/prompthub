# Claude Desktop

Bridge client using `mcpServers` format. Merge install (config includes `globalShortcut` and other preferences).

## Config path

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## Quick setup

```bash
cd app && python -m cli generate claude-desktop
cd app && python -m cli install claude-desktop
```

The `install` command merges the `prompthub` entry into your existing `mcpServers` — other servers and preferences are preserved.

## Files in this directory

- `mcp.json` — Bridge config (source of truth, symlinked to app path)
- `bridge.log` — Symlink to Claude's live MCP bridge log

## External references

- [Claude Desktop MCP docs](https://modelcontextprotocol.io/quickstart/user)
- [Claude Desktop config format](https://docs.anthropic.com/en/docs/claude-desktop/mcp)
