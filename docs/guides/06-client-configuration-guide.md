# Client Setup Guide

## What This Guide Covers

How to connect desktop apps to PromptHub using MCP configs, AI provider settings, and enhancement rules. Every app follows the same pattern:

1. **MCP config** -- tells the app where the PromptHub bridge is and which servers/tools to expose
2. **AI provider** -- points the app's chat interface at PromptHub's OpenAI-compatible API
3. **API key** -- identifies the client for per-app enhancement rules and audit logging

For scripting and developer integration (Python, curl, Node.js, Automator), see [API Integration Examples](../api/integration-examples.md).

---

## Repo-Managed Client Setup

PromptHub no longer uses the old Python config-generator CLI. Client
configuration now lives in repo-managed files under `clients/`, with `setup.sh`
 scripts handling symlinks, copies, or manual instructions.

Typical workflow:

```bash
cd ~/prompthub

./clients/claude/desktop-setup.sh   # Claude Desktop
./clients/claude/code-setup.sh      # Claude Code
./clients/vscode/setup.sh           # VS Code + Copilot
./clients/raycast/setup.sh          # Raycast
./clients/lm-studio/setup.sh        # LM Studio
./clients/codex/setup.sh            # Codex instructions / symlink setup

./scripts/diagnose.sh               # Health and config checks
```

The source of truth is always the file in `clients/`. If a client uses a
symlink strategy, the app reads the repo-managed file directly. If a client
uses a copy or merge strategy, the setup script handles the app-specific step.

### Supported Clients

| Client directory | Target | Setup strategy |
|--------|-------------|------------------|
| `clients/claude/` | Claude Desktop + Claude Code | desktop symlink + code copy |
| `clients/vscode/` | VS Code + Copilot settings | merge / guided file update |
| `clients/raycast/` | `~/.config/raycast/mcp.json` and provider config | symlink |
| `clients/lm-studio/` | `~/.lmstudio/mcp.json` | symlink |
| `clients/codex/` | `~/.codex/config.toml` | manual / TOML |
| `clients/perplexity-desktop/` | Perplexity Desktop config | manual / client-specific |
| `clients/_open-webui/` | Open WebUI example config | placeholder |
| `clients/_zed/` | Zed shared settings | placeholder |
| `clients/_jetbrains/` | JetBrains MCP config | placeholder |
| `clients/_cherry-studio/` | Cherry Studio examples | placeholder |

---

## Install Strategies

PromptHub uses a few different install strategies depending on the client.
Think of it like the difference between copying a recipe into a cookbook
(merge), taping a note to the fridge that points to the recipe (symlink), or
following handwritten instructions for a proprietary app (manual).

### Symlink Install

**Used by:** LM Studio, Raycast, Claude Desktop (for some assets)

The setup script keeps the real config in `clients/<client-name>/` and creates
 a symlink from the app's expected config path to that repo file.

```
~/.lmstudio/mcp.json  -->  ~/prompthub/clients/lm-studio/mcp.json
```

**Why this is useful:**

- The repo is the single source of truth. Every change is tracked in git.
- When you update the config in the repo, the app picks it up on restart.
- No manual copying needed.

**What happens during install:**

1. The setup script backs up any existing config when needed.
2. It points the app's config path at the tracked file in `clients/`.
3. Future edits happen in the repo, not in the app-specific copy.

### Merge Install

**Used by:** VS Code and other clients that keep many unrelated settings in one
file

The setup script or manual process updates only the PromptHub-related section
of the app's existing config file. All other settings are preserved.

**Why this is useful:**

- These apps store many settings in a single config file (editor preferences, themes, keybindings).
- Overwriting the entire file would erase those settings.
- The merge only touches the MCP/servers section.

**What happens during install:**

1. The setup process backs up the existing file when appropriate.
2. It updates the MCP or provider section that PromptHub owns.
3. The rest of the app config stays intact.

### Copy Install

**Used by:** Claude Code

Claude Code reads a project-local `mcp.json`, so the setup script copies the
repo-managed config into the working location that Claude expects.

### Manual Install

**Used by:** Codex, Perplexity Desktop, placeholder clients

Some clients either use TOML, have fast-moving app-specific formats, or are not
fully standardized in this repo yet. For those, PromptHub stores a reference
file in `clients/` and the README explains the manual steps.

### Key points

- Run the client's `setup.sh` from the repo root whenever possible.
- Treat the file in `clients/` as the source of truth.
- Use `./scripts/diagnose.sh` after setup to confirm the router and bridge are healthy.

---

## MCP Config Structure

Every MCP bridge client config follows a similar shape. The exact key names
vary by client, but the bridge entry is the same. Understanding it helps when
you need to inspect or troubleshoot the repo-managed client files.

### Standard format (mcpServers)

Used by Claude Desktop, Claude Code, LM Studio, Raycast, and similar bridge
clients:

```json
{
  "mcpServers": {
    "prompthub": {
      "command": "node",
      "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "AUTHORIZATION": "Bearer sk-prompthub-<client>-001",
        "CLIENT_NAME": "<client>",
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "SERVERS": "memory,context7,sequential-thinking,desktop-commander",
        "EXCLUDE_TOOLS": "duckduckgo,perplexity-comet"
      }
    }
  }
}
```

### VS Code format (mcp > servers)

```json
{
  "mcp": {
    "servers": {
      "prompthub": {
        "command": "node",
        "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
        "env": { "..." }
      }
    }
  }
}
```

### Zed format (context_servers)

```json
{
  "context_servers": {
    "prompthub": {
      "enabled": true,
      "remote": false,
      "command": "node",
      "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
      "env": { "..." }
    }
  }
}
```

### JetBrains format (servers)

```json
{
  "servers": {
    "prompthub": {
      "type": "stdio",
      "command": "node",
      "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
      "env": { "..." }
    }
  }
}
```

### Environment variables

| Field | Purpose |
|-------|---------|
| `AUTHORIZATION` | Bearer token matching a key in `app/configs/api-keys.json` |
| `CLIENT_NAME` | Identifies the client for per-app enhancement rules and audit |
| `PROMPTHUB_URL` | Router address. Use `127.0.0.1`, not `localhost` (avoids IPv6 issues) |
| `SERVERS` | Comma-separated MCP servers to expose. Empty = all. |
| `EXCLUDE_TOOLS` | Comma-separated tool names to hide. Reduces context for smaller models. |

---

## Client Setup

### Claude Desktop

**Type:** Bridge client

Uses MCP for direct tool integration.

```bash
./clients/claude/desktop-setup.sh
```

Or inspect/edit the tracked file in `clients/claude/desktop-mcp.json` before
running setup. Claude Desktop still reads the installed file at
`~/Library/Application Support/Claude/claude_desktop_config.json`.

```json
{
  "mcpServers": {
    "prompthub": {
      "command": "node",
      "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "AUTHORIZATION": "Bearer sk-prompthub-claude-desktop-001",
        "CLIENT_NAME": "claude-desktop",
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "SERVERS": "memory,context7,sequential-thinking,desktop-commander",
        "EXCLUDE_TOOLS": "duckduckgo,perplexity-comet"
      }
    }
  }
}
```

Restart Claude after editing. Verify by asking: "What tools do you have available?"

### Claude Code

**Type:** Bridge client

```bash
./clients/claude/code-setup.sh
```

Claude Code uses the same `mcpServers` format, but the setup script copies the
repo-managed config into the project-local `mcp.json` that Claude Code reads.
The API key and enhancement rule names still use `claude-code`.

### VS Code

**Type:** Bridge client + provider config

**MCP tools** -- use the repo-managed files and setup script:

```bash
./clients/vscode/setup.sh
```

**Chat via OpenAI API** -- add to `settings.json`:

```json
{
  "chat.openaiCompatibleEndpoint": "http://localhost:9090/v1",
  "chat.openaiCompatibleApiKey": "sk-prompthub-vscode-001",
  "chat.openaiCompatibleModel": "qwen3-4b-instruct-2507"
}
```

### Raycast

**Type:** Bridge client (MCP) + OpenAI API (chat), symlink install

Uses the OpenAI-compatible API for AI Chat:

1. **Raycast Settings** > AI > OpenAI Compatible
2. **API Endpoint:** `http://localhost:9090/v1`
3. **API Key:** `sk-prompthub-raycast-001`
4. **Model:** `qwen3-4b-instruct-2507`

For MCP tools, install the bridge config:

```bash
./clients/raycast/setup.sh
```

Test: `Cmd+Space` > "Ask AI" > send a question.

### LM Studio

**Type:** Bridge client, symlink install

Uses MCP for tool access within LM Studio's chat. Config lives at `~/.lmstudio/mcp.json`.

```bash
./clients/lm-studio/setup.sh
```

The setup script keeps the config in `~/prompthub/clients/lm-studio/mcp.json`
and creates a symlink:

```
~/.lmstudio/mcp.json  -->  ~/prompthub/clients/lm-studio/mcp.json
```

You can also verify the symlink manually:

```bash
ls -la ~/.lmstudio/mcp.json
```

After editing or installing, restart MCP servers in LM Studio's Developer tab.

### Zed

**Type:** Placeholder client

Zed is currently tracked as a placeholder under `clients/_zed/`. The examples
still matter because Zed uses the `context_servers` key in a shared JSONC
settings file:

```json
{
  "context_servers": {
    "prompthub": {
      "enabled": true,
      "remote": false,
      "command": "node",
      "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "AUTHORIZATION": "Bearer sk-prompthub-default-001",
        "CLIENT_NAME": "zed",
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "SERVERS": "memory,context7,sequential-thinking,desktop-commander"
      }
    }
  }
}
```

Use `clients/_zed/README.md` for the current manual steps.

### JetBrains IDEs

**Type:** Placeholder client

JetBrains support is tracked under `clients/_jetbrains/`. The config shape is
still useful because JetBrains expects a `servers` object with
`"type": "stdio"`:

```json
{
  "servers": {
    "prompthub": {
      "type": "stdio",
      "command": "node",
      "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "AUTHORIZATION": "Bearer sk-prompthub-jetbrains-001",
        "CLIENT_NAME": "jetbrains",
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "SERVERS": "memory,context7,sequential-thinking,desktop-commander"
      }
    }
  }
}
```

Use `clients/_jetbrains/README.md` for the current manual steps and product-
specific paths.

### Codex

**Type:** Manual config only (TOML format)

Codex uses a TOML config file at `~/.codex/config.toml`. Edit it by hand using
the repo-managed reference in `clients/codex/config.toml` or
`clients/codex/codex-config.toml`.

```toml
[mcp_servers.prompthub]
command = "node"
args = ["/Users/you/prompthub/mcps/prompthub-bridge.js"]
cwd = "~/code/"
enabled = true

[mcp_servers.prompthub.env]
AUTHORIZATION = "Bearer sk-prompthub-codex-001"
CLIENT_NAME = "codex"
PROMPTHUB_URL = "http://127.0.0.1:9090"
SERVERS = "memory,sequential-thinking,desktop-commander,perplexity-comet,context7"
```

Replace `/Users/you/prompthub/` with your actual path. Save the file and restart Codex.

### Cherry Studio

**Type:** Placeholder client

Cherry Studio examples live under `clients/_cherry-studio/`. Use that folder if
you want to adapt the current bridge or HTTP examples manually.

### Open WebUI

**Type:** Placeholder / manual HTTP client

Needs two connections -- chat and tools:

1. **Chat** in Admin > Connections:
   - URL: `http://127.0.0.1:9090/v1`
   - API Key: `sk-prompthub-openwebui-001`

2. **MCP tools** in Admin > Settings > Tools > MCP Servers:
   - URL: `http://127.0.0.1:9090/mcp-direct/mcp`
   - No auth required (local-only endpoint)

Use `GATEWAY_SERVERS` in `app/.env` to limit exposed tools:

```bash
GATEWAY_SERVERS="context7,desktop-commander,sequential-thinking"
```

### OpenCode

**Type:** Historical example

[OpenCode](https://github.com/opencode-ai/opencode) is a terminal-based AI coding agent with strong Git integration. It supports MCP stdio servers natively.

OpenCode is not currently an active client directory in this repo, but the
config shape remains useful if you maintain it separately. Manually edit
`~/.opencode.json` if you still use it:

```json
{
  "mcpServers": {
    "prompthub": {
      "command": "node",
      "args": ["/Users/you/prompthub/mcps/prompthub-bridge.js"],
      "env": [
        "AUTHORIZATION=Bearer sk-prompthub-opencode-001",
        "CLIENT_NAME=opencode",
        "PROMPTHUB_URL=http://127.0.0.1:9090",
        "SERVERS=memory,context7,sequential-thinking,desktop-commander",
        "EXCLUDE_TOOLS=duckduckgo,perplexity-comet"
      ],
      "type": "stdio"
    }
  }
}
```

> **Note:** OpenCode uses `["KEY=VALUE"]` array format for env vars, not the
> `{"KEY": "VALUE"}` dict used by most other clients.

OpenCode can also be paired with an LM Studio provider in the same config file.
Store any API key in keyring rather than hardcoding it in the config file.

### Obsidian

Uses an OpenAI-compatible plugin:

1. **Settings > Community Plugins** > enable > Browse > install an OpenAI plugin
2. Configure: endpoint `http://localhost:9090/v1`, key `sk-prompthub-default-001`, model `qwen3-4b-instruct-2507`

---

## API Keys

### One Key Per App

Each app gets its own key in `app/configs/api-keys.json`:

```json
{
  "keys": {
    "sk-prompthub-claude-desktop-001": {
      "client_name": "claude-desktop",
      "enhance": false,
      "description": "Claude Desktop"
    },
    "sk-prompthub-raycast-001": {
      "client_name": "raycast",
      "enhance": false,
      "description": "Raycast Commands"
    }
  }
}
```

Benefits:
- Disable one app without affecting others
- Per-app enhancement settings
- Audit trail per client
- Revoke access individually

### The `enhance` Flag

Set `"enhance": true` to automatically rewrite prompts before they reach the model. The enhancement model (`qwen3-4b-instruct-2507`) improves clarity and specificity. Set to `false` for lower latency.

### Reload Keys

After editing `api-keys.json`, reload without restarting:

```bash
curl -X POST http://localhost:9090/v1/api-keys/reload
```

---

## Enhancement Rules

Per-client prompt rewriting behavior is configured in `app/configs/enhancement-rules.json`:

```json
{
  "default": {
    "model": "qwen3-4b-instruct-2507",
    "system_prompt": "You are a prompt engineer. Rewrite the user's prompt to be clearer...",
    "temperature": 0.3,
    "max_tokens": 500,
    "privacy_level": "local_only"
  },
  "clients": {
    "raycast": {
      "temperature": 0.3,
      "max_tokens": 300,
      "system_prompt": "...action-oriented, CLI-style, under 150 words...",
      "privacy_level": "free_ok"
    }
  }
}
```

| Field | Purpose |
|-------|---------|
| `model` | Which LLM rewrites the prompt (all clients currently share the same model) |
| `system_prompt` | Instructions for the rewriter -- tailored per client |
| `temperature` | Randomness (0.2 for code, 0.3 for general, 0.5 for creative) |
| `max_tokens` | Maximum length of the rewritten prompt |
| `privacy_level` | `local_only` (never leaves machine), `free_ok` (cloud fallback allowed), `any` |

### Privacy Levels

| Level | Behavior |
|-------|----------|
| `local_only` | Prompts never leave localhost. Cloud fallback disabled. Default for most clients. |
| `free_ok` | Falls back to OpenRouter free-tier if LM Studio is down. Used by Raycast, Perplexity. |
| `any` | Any cloud provider allowed (not currently used). |

The `X-Privacy-Level` header can downgrade privacy (more restrictive) but never upgrade it.

---

## Troubleshooting

### "Cannot connect to localhost:9090"

```bash
lsof -i :9090                              # Check if router is running
curl http://localhost:9090/health           # Verify health
./scripts/diagnose.sh                      # Full stack check
```

### "Invalid API key"

```bash
# Verify key exists
grep "sk-prompthub" ~/prompthub/app/configs/api-keys.json

# Reload keys without restart
curl -X POST http://localhost:9090/v1/api-keys/reload
```

### "Model not found"

```bash
lms ls                                      # List available models
lms get qwen3-4b-instruct-2507                 # Download missing model
```

### "Enhancement is slow"

1. Set `"enhance": false` in the app's API key entry
2. Check if LM Studio is busy: `lms ps`

### Zed config has parse errors after install

Zed uses JSONC (JSON with comments). Check `clients/_zed/README.md` for the
current manual process and back up your settings before editing.

### JetBrains IDE does not detect MCP config

JetBrains products often use product-specific config paths. Check
`clients/_jetbrains/README.md` for the current manual instructions.

### Codex config still does not load

Codex uses TOML, not JSON. Edit `~/.codex/config.toml` by hand and compare it
to the reference in the [Codex section](#codex) above.

---

## Summary

| App | Connection | MCP Tools | AI Provider | Install Strategy |
|-----|-----------|-----------|-------------|------------------|
| Claude Desktop | MCP bridge | Yes | No (uses own models) | desktop setup script |
| Claude Code | MCP bridge | Yes | No | code setup script |
| VS Code | MCP bridge + OpenAI API | Yes | Yes | setup script |
| Raycast | MCP bridge + OpenAI API | Yes | Yes | symlink setup script |
| LM Studio | MCP bridge | Yes | No (is the model server) | symlink setup script |
| Codex | MCP bridge (TOML) | Yes | No | manual |
| Perplexity Desktop | MCP bridge | Yes | No | manual / client-specific |
| Zed | MCP bridge (context_servers) | Yes | No | placeholder |
| JetBrains | MCP bridge (servers) | Yes | No | placeholder |
| Cherry Studio | bridge + HTTP examples | Partial | Partial | placeholder |
| Open WebUI | OpenAI API + Streamable HTTP | Yes | Yes | placeholder / manual |
| Obsidian | OpenAI API | No | Yes | plugin setup |

---

**Next:** [Troubleshooting Guide](05-troubleshooting-guide.md) | **Developer:** [API Integration Examples](../api/integration-examples.md)
