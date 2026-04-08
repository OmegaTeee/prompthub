# Client Setup Guide

## What This Guide Covers

How to connect desktop apps to PromptHub using MCP configs, AI provider settings, and enhancement rules. Every app follows the same pattern:

1. **MCP config** -- tells the app where the PromptHub bridge is and which servers/tools to expose
2. **AI provider** -- points the app's chat interface at PromptHub's OpenAI-compatible API
3. **API key** -- identifies the client for per-app enhancement rules and audit logging

For scripting and developer integration (Python, curl, Node.js, Automator), see [API Integration Examples](../api/integration-examples.md).

---

## CLI Config Manager

PromptHub includes a CLI that generates, installs, and validates MCP configs. Use it instead of editing JSON by hand.

```bash
cd ~/prompthub/app

python -m cli list                         # Show all 11 clients with install strategy
python -m cli generate claude-desktop      # Print config JSON (preview)
python -m cli install claude-desktop       # Write config to the app's config file
python -m cli validate claude-desktop      # Check for issues
python -m cli diff claude-desktop          # Compare installed vs. generated
python -m cli diagnose                     # Full stack health check
```

| Command | What It Does |
|---------|-------------|
| `generate <client>` | Print MCP config JSON. Merges API key and enhancement rules automatically. |
| `install <client>` | Write config into the app's file. `--dry-run` to preview, `--force` to replace. |
| `validate <client>` | Check path safety, env vars, bridge existence, API key validity. |
| `diff <client>` | Unified diff between installed and generated. Useful after manual edits. |
| `list` | All clients, config paths, API keys, install strategy, and privacy levels. |
| `diagnose` | Router, bridge, Node.js, LM Studio -- full stack check. |

### Supported Clients

| Client | Config Path | Install Strategy |
|--------|-------------|------------------|
| `claude-desktop` | `~/Library/Application Support/Claude/claude_desktop_config.json` | merge |
| `claude-code` | `~/.claude.json` | merge |
| `cursor` | `~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/mcp.json` | symlink |
| `vscode` | VS Code MCP settings | merge |
| `raycast` | `~/.config/raycast/mcp.json` | symlink |
| `lm-studio` | `~/.lmstudio/mcp.json` | symlink |
| `zed` | `~/.config/zed/settings.json` | merge |
| `jetbrains` | `~/.config/JetBrains/mcp.json` | merge |
| `codex` | `~/.codex/config.toml` | manual only |
| `cherry-studio` | `~/.prompthub/cherry-studio.json` | merge |
| `open-webui` | `~/.prompthub/open-webui.json` | merge |
| `opencode` | `~/.opencode.json` | merge |

### Generate with Options

```bash
# Limit which MCP servers are exposed
python -m cli generate claude-desktop --servers "context7,desktop-commander"

# Exclude heavy tools for smaller models
python -m cli generate raycast --exclude-tools "duckduckgo,perplexity-comet"

# Override the API key
python -m cli generate vscode --api-key "sk-prompthub-vscode-001"
```

### Recommended Workflow

```bash
python -m cli install claude-desktop --dry-run   # 1. Preview
python -m cli install claude-desktop              # 2. Install
python -m cli validate claude-desktop             # 3. Verify
python -m cli diff claude-desktop                 # 4. Check drift later
```

---

## Install Strategies

When you run `python -m cli install <client>`, the CLI uses one of two strategies depending on the client. Think of it like the difference between copying a recipe into a cookbook (merge) versus taping a note on the fridge that says "recipe is on the counter" (symlink).

### Symlink Install

**Used by:** LM Studio, Cursor, Raycast

The CLI writes the generated config to a file inside the repo (`clients/<client-name>/`). Then it creates a symlink from the app's expected config path to that repo file.

```
~/.lmstudio/mcp.json  -->  ~/prompthub/clients/lm-studio/mcp.json
```

**Why this is useful:**

- The repo is the single source of truth. Every change is tracked in git.
- When you update the config in the repo, the app picks it up on restart.
- No manual copying needed.

**What happens during install:**

1. The CLI backs up any existing config file (creates a `.bak` copy).
2. It writes the generated config to `clients/<client-name>/`.
3. It replaces the app's config path with a symlink to the repo file.

### Merge Install

**Used by:** Claude Desktop, Claude Code, VS Code, Zed, JetBrains

The CLI reads the app's existing config file and merges the PromptHub bridge entry into it. All other settings in the file are preserved.

**Why this is useful:**

- These apps store many settings in a single config file (editor preferences, themes, keybindings).
- Overwriting the entire file would erase those settings.
- The merge only touches the MCP/servers section.

**What happens during install:**

1. The CLI backs up the existing config file (creates a `.bak` copy).
2. It reads the file and parses the JSON (or JSONC for Zed).
3. It adds or updates the PromptHub bridge entry inside the correct key path.
4. It writes the merged result back.

### Key points

- Use `--dry-run` with any install command to preview changes without writing files.
- Use `--force` to replace the entire servers section instead of merging.
- Codex does not support either strategy. Edit its TOML config by hand.

---

## MCP Config Structure

Every MCP bridge client config follows a similar shape. The exact key names vary by client, but the bridge entry is the same. The CLI generates this for you, but understanding it helps when troubleshooting.

### Standard format (mcpServers)

Used by Claude Desktop, Claude Code, Cursor, LM Studio, and Raycast:

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

**Type:** Bridge client, merge install

Uses MCP for direct tool integration.

```bash
python -m cli install claude-desktop
```

Or manually edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

**Type:** Bridge client, merge install

```bash
python -m cli install claude-code
```

Config lives at `~/.claude.json`. Uses the `mcpServers` key, same format as Claude Desktop.

### VS Code

**Type:** Bridge client, merge install

**MCP tools** -- edit `.vscode/mcp.json` or use the CLI:

```bash
python -m cli install vscode
```

**Chat via OpenAI API** -- add to `settings.json`:

```json
{
  "chat.openaiCompatibleEndpoint": "http://localhost:9090/v1",
  "chat.openaiCompatibleApiKey": "sk-prompthub-vscode-001",
  "chat.openaiCompatibleModel": "qwen3-4b-instruct-2507"
}
```

### Cursor

**Type:** Bridge client, symlink install

```bash
python -m cli install cursor
```

The CLI writes config to `~/prompthub/clients/cursor/` and symlinks the app's config path to it. Cursor reads MCP settings from `~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/mcp.json`.

### Raycast

**Type:** Bridge client (MCP) + OpenAI API (chat), symlink install

Uses the OpenAI-compatible API for AI Chat:

1. **Raycast Settings** > AI > OpenAI Compatible
2. **API Endpoint:** `http://localhost:9090/v1`
3. **API Key:** `sk-prompthub-raycast-001`
4. **Model:** `qwen3-4b-instruct-2507`

For MCP tools, install the bridge config:

```bash
python -m cli install raycast
```

Test: `Cmd+Space` > "Ask AI" > send a question.

### LM Studio

**Type:** Bridge client, symlink install

Uses MCP for tool access within LM Studio's chat. Config lives at `~/.lmstudio/mcp.json`.

```bash
python -m cli install lm-studio
```

The CLI writes the config to `~/prompthub/clients/lm-studio/mcp.json` and creates a symlink:

```
~/.lmstudio/mcp.json  -->  ~/prompthub/clients/lm-studio/mcp.json
```

You can also verify the symlink manually:

```bash
ls -la ~/.lmstudio/mcp.json
```

To preview what the CLI will generate:

```bash
python -m cli generate lm-studio
```

This outputs the `mcpServers` JSON with the bridge entry.

After editing or installing, restart MCP servers in LM Studio's Developer tab.

### Zed

**Type:** Bridge client, merge install

Zed stores all settings -- including MCP servers -- in a single file at `~/.config/zed/settings.json`. This file uses JSONC format, which means it allows `//` comments and trailing commas. Standard JSON parsers cannot read it, but the CLI handles JSONC automatically.

```bash
python -m cli install zed
```

To preview the generated config:

```bash
python -m cli generate zed
```

This outputs the `context_servers` JSON. Zed uses a unique key name compared to other clients:

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

**Important: JSONC handling.** Zed's `settings.json` contains `//` comments and trailing commas. The CLI strips these before parsing and preserves all your other Zed settings (themes, fonts, keybindings, etc.) during the merge. However, after the CLI writes the merged file, the comments and trailing commas are removed. If you want to keep your comments, make a backup first or use `--dry-run` to preview.

After installing, restart Zed or reload the window (`Cmd+Shift+P` > "Reload") to pick up the new MCP config.

### JetBrains IDEs

**Type:** Bridge client, merge install

Works with all JetBrains IDEs: IntelliJ IDEA, PyCharm, WebStorm, GoLand, and others. The default config path is `~/.config/JetBrains/mcp.json`.

```bash
python -m cli install jetbrains
```

To preview the generated config:

```bash
python -m cli generate jetbrains
```

This outputs the `servers` JSON with a `"type": "stdio"` field:

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

**IDE-specific config paths.** Some JetBrains IDEs store their config in a product-specific folder (for example, `~/Library/Application Support/JetBrains/IntelliJIdea2025.1/`). If your IDE does not read from the default path, use the `--config` flag to point to the right file:

```bash
python -m cli install jetbrains --config ~/Library/Application\ Support/JetBrains/IntelliJIdea2025.1/mcp.json
```

After installing, restart your IDE to load the new MCP tools.

### Codex

**Type:** Manual config only (TOML format)

Codex uses a TOML config file at `~/.codex/config.toml`. The CLI cannot generate or install this config automatically because it is not JSON. You must edit the file by hand.

Running `generate` or `install` will show an error:

```bash
python -m cli generate codex
# Error: Codex uses TOML config. Edit clients/codex/config.toml manually.
```

A reference config file is included in the repo at `~/prompthub/clients/codex-config.toml`. Copy the relevant sections into your own config:

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

**Type:** HTTP client, merge install

Cherry Studio connects to PromptHub over HTTP, similar to Open WebUI. It does not use the stdio bridge. Instead, it connects through the OpenAI-compatible API and the Responses API endpoint (`/v1/responses`).

```bash
python -m cli install cherry-studio
```

To preview the generated config:

```bash
python -m cli generate cherry-studio
```

This outputs HTTP connection settings (not bridge config):

```json
{
  "cherry_studio": {
    "api_base_url": "http://127.0.0.1:9090/v1",
    "responses_endpoint": "http://127.0.0.1:9090/v1/responses",
    "api_key": "sk-prompthub-cherry-001"
  }
}
```

Config is stored at `~/.prompthub/cherry-studio.json`. After installing, configure Cherry Studio to point at the `api_base_url` and use the API key shown above.

### Open WebUI

**Type:** HTTP client, merge install

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

**Type:** Bridge client, merge install

[OpenCode](https://github.com/opencode-ai/opencode) is a terminal-based AI coding agent with strong Git integration. It supports MCP stdio servers natively.

```bash
python -m cli install opencode
```

Or manually edit `~/.opencode.json`:

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

> **Note:** OpenCode uses `["KEY=VALUE"]` array format for env vars, not the `{"KEY": "VALUE"}` dict used by other clients. The CLI generates the correct format automatically.

OpenCode also supports an LM Studio provider in the same config file. See `clients/opencode/opencode.json` for a template. Store your LM Studio API key in keyring rather than the config file.

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
python -m cli diagnose                      # Full stack check
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

Zed uses JSONC (JSON with comments). After the CLI merges your config, comments and trailing commas are stripped. This does not affect functionality, but it changes the file format. To avoid surprises, preview with `--dry-run` first:

```bash
python -m cli install zed --dry-run
```

### JetBrains IDE does not detect MCP config

JetBrains products sometimes use product-specific config paths. Try pointing to the IDE's own folder:

```bash
python -m cli install jetbrains --config ~/Library/Application\ Support/JetBrains/PyCharm2025.1/mcp.json
```

### Codex CLI says "NotImplementedError"

This is expected. Codex uses TOML, not JSON. Edit `~/.codex/config.toml` by hand. See the [Codex section](#codex) above for the reference config.

---

## Summary

| App | Connection | MCP Tools | AI Provider | Install Strategy |
|-----|-----------|-----------|-------------|------------------|
| Claude Desktop | MCP bridge | Yes | No (uses own models) | merge |
| Claude Code | MCP bridge | Yes | No | merge |
| VS Code | MCP bridge + OpenAI API | Yes | Yes | merge |
| Cursor | MCP bridge | Yes | Yes | symlink |
| Raycast | MCP bridge + OpenAI API | Yes | Yes | symlink |
| LM Studio | MCP bridge | Yes | No (is the model server) | symlink |
| Zed | MCP bridge (context_servers) | Yes | No | merge |
| JetBrains | MCP bridge (servers) | Yes | No | merge |
| Codex | MCP bridge (TOML) | Yes | No | manual |
| Cherry Studio | HTTP (Responses API) | No | Yes | merge |
| Open WebUI | OpenAI API + Streamable HTTP | Yes | Yes | merge |
| Obsidian | OpenAI API | No | Yes | -- |

---

**Next:** [Troubleshooting Guide](05-troubleshooting-guide.md) | **Developer:** [API Integration Examples](../api/integration-examples.md)
