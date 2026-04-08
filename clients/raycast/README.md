# Raycast

Bridge client using `mcpServers` format. **Symlink install** (MCP-only config file).

## Config path

```
~/.config/raycast/mcp.json  ->  ~/prompthub/clients/raycast/mcp.json
```

## Quick setup

```bash
cd app && python -m cli generate raycast
cd app && python -m cli install raycast
```

The `install` command writes to `clients/raycast/mcp.json` and creates a symlink at the app path.

## Files in this directory

- `mcp.json` — Bridge config (source of truth, symlinked to app path)
- `provider.yaml` — Raycast AI Chat custom provider config (points to PromptHub `/v1/` proxy)

## Privacy level

Raycast is configured with `privacy_level: free_ok` — prompts may be enhanced via OpenRouter free-tier when the local LLM is unavailable.

## External references

- [Raycast MCP docs](https://developers.raycast.com/model-context-protocol)
