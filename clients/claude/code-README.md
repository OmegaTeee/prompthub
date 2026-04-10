# Claude Code

Bridge client using `mcpServers` format. Merge install (config file shared with other Claude Code settings).

## Config path

```
~/.claude.json
```

## Quick setup

```bash
./clients/claude/code-setup.sh
```

## Files in this directory

- `mcp.json` — Bridge config (source of truth)
- `project.json` — Symlink to repo-level `.mcp.json` (project-scoped MCP config)

## External references

- [Claude Code MCP docs](https://docs.anthropic.com/en/docs/claude-code/mcp)
