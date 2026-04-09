# JetBrains

Bridge client using `servers` format with `"type": "stdio"`. Placeholder/manual
setup.

## Config path

```
~/.config/JetBrains/mcp.json
```

This is the **global** MCP config for JetBrains IDEs (2024.3+). If you want an
IDE-specific file, adapt the same JSON shape to that IDE's MCP config path.

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
