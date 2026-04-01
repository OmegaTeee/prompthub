# Client Setup Guide

## What This Guide Covers

How to connect desktop apps to PromptHub using MCP configs, AI provider settings, and enhancement rules. Every app follows the same pattern:

1. **MCP config** — tells the app where the PromptHub bridge is and which servers/tools to expose
2. **AI provider** — points the app's chat interface at PromptHub's OpenAI-compatible API
3. **API key** — identifies the client for per-app enhancement rules and audit logging

For scripting and developer integration (Python, curl, Node.js, Automator), see [API Integration Examples](../api/integration-examples.md).

---

## CLI Config Manager

PromptHub includes a CLI that generates, installs, and validates MCP configs. Use it instead of editing JSON by hand.

```bash
cd ~/prompthub/app

python -m cli list                         # Show all clients and config paths
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
| `list` | All clients, config paths, API keys, and privacy levels. |
| `diagnose` | Router, bridge, Node.js, LM Studio — full stack check. |

### Supported Clients

| Client | Config Path |
|--------|-------------|
| `claude-desktop` | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| `claude-code` | `~/.claude.json` |
| `cursor` | `~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/mcp.json` |
| `vscode` | VS Code MCP settings |
| `raycast` | `~/.config/raycast/mcp.json` |
| `open-webui` | `~/.prompthub/open-webui.json` |

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

## MCP Config Structure

Every MCP client config follows the same shape. The CLI generates this for you, but understanding it helps when troubleshooting.

```json
{
  "mcpServers": {
    "prompthub-bridge": {
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

| Field | Purpose |
|-------|---------|
| `AUTHORIZATION` | Bearer token matching a key in `app/configs/api-keys.json` |
| `CLIENT_NAME` | Identifies the client for per-app enhancement rules and audit |
| `PROMPTHUB_URL` | Router address. Use `127.0.0.1`, not `localhost` (avoids IPv6 issues) |
| `SERVERS` | Comma-separated MCP servers to expose. Empty = all. |
| `EXCLUDE_TOOLS` | Comma-separated tool names to hide. Reduces context for smaller models. |

### Symlink Convention

Canonical configs live in `~/prompthub/mcps/configs/`. Each app reads through a symlink at its expected path:

```
~/.lmstudio/mcp.json        → ~/prompthub/mcps/configs/lm-studio.json
~/.config/raycast/mcp.json  → ~/prompthub/mcps/configs/raycast-mcp.json
```

Edit the repo file; the app picks up changes on restart.

---

## Client Setup

### Claude Desktop

Uses MCP for direct tool integration.

```bash
python -m cli install claude-desktop
```

Or manually edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "prompthub-bridge": {
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

### VS Code

**MCP tools** — edit `.vscode/mcp.json` or use the CLI:

```bash
python -m cli install vscode
```

**Chat via OpenAI API** — add to `settings.json`:

```json
{
  "chat.openaiCompatibleEndpoint": "http://localhost:9090/v1",
  "chat.openaiCompatibleApiKey": "sk-prompthub-vscode-001",
  "chat.openaiCompatibleModel": "qwen/qwen3-4b-2507"
}
```

### Raycast

Uses the OpenAI-compatible API for AI Chat:

1. **Raycast Settings** > AI > OpenAI Compatible
2. **API Endpoint:** `http://localhost:9090/v1`
3. **API Key:** `sk-prompthub-raycast-001`
4. **Model:** `qwen/qwen3-4b-2507`

Test: `Cmd+Space` > "Ask AI" > send a question.

### LM Studio

Uses MCP for tool access within LM Studio's chat. Config lives at `~/.lmstudio/mcp.json` (symlinked to repo).

```bash
ls -la ~/.lmstudio/mcp.json
# Should show: → ~/prompthub/mcps/configs/lm-studio.json
```

After editing, restart MCP servers in LM Studio's Developer tab.

### Open WebUI

Needs two connections — chat and tools:

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

### Obsidian

Uses an OpenAI-compatible plugin:

1. **Settings > Community Plugins** > enable > Browse > install an OpenAI plugin
2. Configure: endpoint `http://localhost:9090/v1`, key `sk-prompthub-default-001`, model `qwen/qwen3-4b-2507`

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

Set `"enhance": true` to automatically rewrite prompts before they reach the model. The enhancement model (`qwen/qwen3-4b-2507`) improves clarity and specificity. Set to `false` for lower latency.

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
    "model": "qwen/qwen3-4b-2507",
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
| `system_prompt` | Instructions for the rewriter — tailored per client |
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
lms get qwen/qwen3-4b-2507                 # Download missing model
```

### "Enhancement is slow"

1. Set `"enhance": false` in the app's API key entry
2. Check if LM Studio is busy: `lms ps`

---

## Summary

| App | Connection | MCP Tools | AI Provider |
|-----|-----------|-----------|-------------|
| Claude Desktop | MCP bridge | Yes | No (uses own models) |
| Claude Code | MCP bridge | Yes | No |
| VS Code | MCP bridge + OpenAI API | Yes | Yes |
| Cursor | MCP bridge | Yes | Yes |
| Raycast | OpenAI API | Via bridge | Yes |
| LM Studio | MCP bridge | Yes | No (is the model server) |
| Open WebUI | OpenAI API + Streamable HTTP | Yes | Yes |
| Obsidian | OpenAI API | No | Yes |

---

**Next:** [Troubleshooting Guide](05-troubleshooting-guide.md) | **Developer:** [API Integration Examples](../api/integration-examples.md)
