# Open WebUI

HTTP client — connects via the OpenAI-compatible proxy (`/v1/`) and Streamable HTTP MCP endpoint (`/mcp-direct/mcp`). No stdio bridge.

## Config path

```
~/.prompthub/open-webui.json
```

## Quick setup

```bash
cd app && python -m cli generate open-webui
cd app && python -m cli install open-webui
cd app && python -m cli validate open-webui
```

## Files in this directory

- `example.toml` — Open WebUI Docker/config reference

## Detailed guide

See [docs/guides/09-open-webui-guide.md](../../docs/guides/09-open-webui-guide.md) for full setup including LaunchAgent, GATEWAY_SERVERS filter, and dashboard integration.

## External references

- [Open WebUI repo](https://github.com/open-webui/open-webui)
- [Open WebUI docs](https://docs.openwebui.com)
