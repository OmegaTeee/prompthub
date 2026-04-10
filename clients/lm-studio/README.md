# LM Studio

Bridge client using `mcpServers` format. **Symlink install** (MCP-only config file).

## Config path

```
~/.lmstudio/mcp.json  ->  ~/prompthub/clients/lm-studio/mcp.json
```

## Quick setup

```bash
./clients/lm-studio/setup.sh
```

The setup script creates the symlink at `~/.lmstudio/mcp.json`.

## Notes

LM Studio also serves as the **local LLM backend** for PromptHub (port 1234). The MCP bridge config here is for LM Studio as an MCP *client* — using PromptHub's tools within LM Studio's chat.

## Files in this directory

- `mcp.json` — Bridge config (source of truth, symlinked to app path)
- `provider.json` — LM Studio provider/model settings
- `lm-studio-llm.txt` — Full upstream docs (14K lines, from lmstudio.ai)

## External references

- [LM Studio MCP docs](https://lmstudio.ai/docs/app/plugins/mcp)
- [LM Studio full docs](https://lmstudio.ai/docs)
