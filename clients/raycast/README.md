# Raycast

Bridge client using `mcpServers` format. **Symlink install** (MCP-only config file).

## MCP configuration

```txt
~/.config/raycast/mcp.json  ->  ~/prompthub/clients/raycast/mcp.json
```

## Provider configuration

```txt
~/.config/raycast/ai/providers.yaml  ->  ~/prompthub/clients/raycast/providers.yaml
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

- [Raycast Manual - MCP Guide](https://manual.raycast.com/model-context-protocol)

- [Raycast Manual - AI Chat Custom Providers](https://manual.raycast.com/ai/ai-chat#custom-providers)

- [Raycast API Docs - OAuth Authorization](https://developers.raycast.com/api-reference/oauth#authorizing)

- [Raycast API Docs - OAuth Utils](https://developers.raycast.com/utilities/oauth)
