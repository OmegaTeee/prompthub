# Zed

Bridge client using `context_servers` format (unique to Zed). Merge install — Zed's `settings.json` contains many non-MCP preferences.

## Config path

```
~/.config/zed/settings.json
```

## Quick setup

```bash
cd app && python -m cli generate zed
cd app && python -m cli install zed
```

The `install` command merges the `prompthub` entry into the existing `context_servers` section. Other Zed settings (fonts, themes, language models, etc.) are preserved.

## JSONC format

Zed's `settings.json` uses **JSONC** (JSON with Comments) — `//` line comments and trailing commas are valid. The CLI's installer handles this automatically by stripping comments before parsing.

## Config format

Unlike most clients that use `mcpServers`, Zed uses `context_servers` with extra fields:

```jsonc
// In ~/.config/zed/settings.json
{
  "context_servers": {
    "prompthub": {
      "enabled": true,
      "remote": false,
      "command": "node",
      "args": ["/Users/<you>/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "CLIENT_NAME": "zed"
      }
    }
  }
}
```

## Files in this directory

- `settings.json` — Zed editor settings (provider config, context servers)
- `ide-settings.json` — Alternative Zed IDE settings
- `zed-llm.txt` — LLM knowledge file (context servers docs)

## External references

- [Zed MCP docs](https://zed.dev/docs/ai/mcp) (context servers, tool permissions, agent profiles)
- [Zed AI configuration](https://zed.dev/docs/ai/configuration)
