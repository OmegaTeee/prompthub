# Client Configurations

Per-client directories containing MCP bridge configs, provider configs, setup scripts, and knowledge files. See [docs/glossary.md](../docs/glossary.md) for definitions of bridge, proxy, client, and llm.txt.

Active clients are unprefixed. Placeholder/draft clients use a `_` prefix.
This folder is still evolving. For Claude agents, use
`.claude/skills/client-setup/SKILL.md` as the setup/update workflow when
activating or repairing a client. Other agents should follow the same pattern
manually from this README plus `clients/default/`.

## Structure

```
clients/
  <client-name>/
    mcp.json            MCP bridge config (source of truth)
    setup.sh            Install script (symlink, copy, or manual instructions)
    uninstall.sh        Reverse script (removes symlink, restores backup)
    README.md           Client-specific notes
    <name>-llm.txt      LLM knowledge file (optional)
```

## Active Clients

| Directory | Transport | Strategy | Config Path |
|-----------|-----------|----------|-------------|
| `claude/` | bridge | symlink + copy | Desktop: `~/Library/.../Claude/claude_desktop_config.json`, Code: project root `mcp.json` |
| `codex/` | bridge | symlink | `~/.codex/config.toml` |
| `lm-studio/` | bridge | symlink | `~/.lmstudio/mcp.json` |
| `perplexity-desktop/` | bridge | symlink | — |
| `raycast/` | bridge | symlink | `~/.config/raycast/mcp.json` |
| `vscode/` | bridge | merge | `~/Library/.../Code/.../mcp_settings.json` (includes Copilot configs) |
| `default/` | bridge | template | Template scripts for new clients |

Backward-compat symlinks: `claude-code` → `claude/`, `claude-desktop` → `claude/`

## Placeholder Clients (`_` prefix)

| Directory | Transport | Notes |
|-----------|-----------|-------|
| `_cherry-studio/` | bridge + http | Electron dialog, no standalone config file |
| `_jetbrains/` | bridge | No enhancement rule yet |
| `_open-webui/` | http (OpenAI proxy) | No MCP bridge — connects via `/v1/` |
| `_zed/` | bridge | Manual paste (JSONC shared settings) |

## Setup

```bash
# Run a client's setup script
./clients/raycast/setup.sh           # creates symlink
./clients/claude/desktop-setup.sh    # creates symlink
./clients/claude/code-setup.sh       # copies config

# Reverse
./clients/raycast/uninstall.sh       # removes symlink, restores backup
./clients/raycast/uninstall.sh --purge  # also deletes backup
```

## Adding a New Client

If you are using Claude, start with `.claude/skills/client-setup/SKILL.md`.
Otherwise, copy from `clients/default/` and follow the same workflow manually:

```bash
cp -r clients/default clients/<name>
# Edit setup.sh and uninstall.sh — customize CLIENT_NAME, CONFIG_FILE, APP_CONFIG
```

## Symlink Convention

```
clients/raycast/mcp.json              ← real file (git-tracked)
~/.config/raycast/mcp.json            ← symlink → ~/prompthub/clients/raycast/mcp.json
```

Source in the project, symlink at the client location. Run `setup.sh` to create the link; `uninstall.sh` to reverse it.

## Diagnostics

```bash
./scripts/diagnose.sh
```
