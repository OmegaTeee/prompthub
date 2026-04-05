# Client Configurations

Per-client directories containing MCP bridge configs, application settings, knowledge files, and setup scripts.

## Structure

Each client has its own directory:

```
clients/
  <client-name>/
    setup.sh            Setup script (symlink or instructions)
    README.md           Setup instructions and external doc links
    mcp.json            MCP bridge config (source of truth)
    provider.yaml       App-specific settings (if applicable)
    <client>-llm.txt    LLM knowledge file (if applicable)
```

## Setup

Each client has a `setup.sh` that either creates a symlink or prints setup instructions:

```bash
# Symlink clients (automated)
./clients/lm-studio/setup.sh
./clients/claude-desktop/setup.sh
./clients/cursor/setup.sh

# Informational clients (prints instructions)
./clients/zed/setup.sh
./clients/cherry-studio/setup.sh
```

## Diagnostics

Check all client configs and system health:

```bash
./scripts/diagnose.sh
```

## Clients

| Directory | Transport | Setup | Config Path |
|-----------|-----------|-------|-------------|
| `claude-desktop/` | bridge | symlink | `~/Library/.../Claude/claude_desktop_config.json` |
| `claude-code/` | bridge | copy | Project root `mcp.json` |
| `cursor/` | bridge | symlink | `~/Library/.../Cursor/.../mcp.json` |
| `vscode/` | bridge | manual | `~/Library/.../Code/.../mcp_settings.json` |
| `raycast/` | bridge | symlink | `~/.config/raycast/mcp.json` |
| `lm-studio/` | bridge | symlink | `~/.lmstudio/mcp.json` |
| `zed/` | bridge | manual | `~/.config/zed/settings.json` |
| `jetbrains/` | bridge | symlink | `~/.config/JetBrains/mcp.json` |
| `cherry-studio/` | bridge + http | manual | GUI (LevelDB) |
| `codex/` | bridge | manual | `~/.codex/config.toml` |
| `open-webui/` | http | manual | Open WebUI admin panel |
| `opencode/` | bridge | symlink | `~/.opencode.json` |
| `copilot/` | bridge | manual | VS Code / project config |
| `openclaw/` | bridge | -- | -- |
| `perplexity-desktop/` | bridge | -- | -- |
| `default/` | bridge | -- | Fallback for unrecognized clients |

## Symlink convention

```
clients/lm-studio/mcp.json           <- real file (git-tracked)
~/.lmstudio/mcp.json                 <- symlink -> ~/prompthub/clients/lm-studio/mcp.json
```

Source in the project, symlink at the client location. Run the client's `setup.sh` to create the link.
