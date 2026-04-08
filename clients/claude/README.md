# Claude (Code + Desktop)

Merged directory for both Claude clients. Symlinks at `clients/claude-code` and
`clients/claude-desktop` point here for backward compatibility.

## Files

# 📁 ⚙️  📔 📓 📒 📝 📄 📃

| File | Client | Purpose |
|---|---|---|
| `code-mcp.json` | Claude Code | MCP bridge config (includes skills-mcp, fetch) |
| `code-project.json` | Claude Code | Project-level Claude settings |
| `code-setup.sh` | Claude Code | Copies config to repo root `mcp.json` |
| `desktop-mcp.json` | Claude Desktop | MCP bridge config + app preferences |
| `desktop-setup.sh` | Claude Desktop | Symlinks to `~/Library/Application Support/Claude/` |
| `desktop-config.json.example` | Claude Desktop | Example config for reference |
| `desktop-bridge.log` | Claude Desktop | Bridge debug log |

## Setup

```bash
./clients/claude/code-setup.sh       # or: ./clients/claude-code/code-setup.sh
./clients/claude/desktop-setup.sh    # or: ./clients/claude-desktop/desktop-setup.sh
```

## Notes

- API keys in `api-keys.json` are still `client_name: "claude-code"` and `"claude-desktop"`
- Enhancement rules in `enhancement-rules.json` are still keyed by `claude-code` and `claude-desktop`
- The symlinks (`claude-code` → `claude/`, `claude-desktop` → `claude/`) mean old paths still work
