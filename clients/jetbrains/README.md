# JetBrains

Bridge client using `servers` format with `"type": "stdio"`. Merge install.

## Config path

```
~/.config/JetBrains/mcp.json
```

This is the **global** MCP config for JetBrains IDEs (2024.3+). IDE-specific paths can be targeted with `--config`:

```bash
cd app && python -m cli install jetbrains --config ~/.config/JetBrains/IntelliJIdea2025.1/mcp.json
```

## Quick setup

```bash
cd app && python -m cli generate jetbrains
cd app && python -m cli install jetbrains
```

## Config format

JetBrains uses `servers` (not `mcpServers`) with an explicit `type` field:

```json
{
  "servers": {
    "prompthub": {
      "type": "stdio",
      "command": "node",
      "args": ["/Users/<you>/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "CLIENT_NAME": "jetbrains"
      }
    }
  }
}
```

## Files in this directory

- `mcp.json` — Bridge config
- `ide-settings.json` — IDE-specific settings placeholder
- `jetbrains-llm.txt` — LLM knowledge file (MCP setup docs)

## Supported IDEs

IntelliJ IDEA, WebStorm, PyCharm, GoLand, PhpStorm, RubyMine, CLion, Rider, DataGrip (all 2024.3+).

## External references

- [JetBrains AI Assistant MCP docs](https://www.jetbrains.com/help/ai-assistant/mcp.html)
