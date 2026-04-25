# VS Code + GitHub Copilot

Bridge client using `mcp.servers` format. VS Code settings contain many non-MCP preferences — setup.sh handles the merge.

## Files in this directory

- `mcp.json` — MCP bridge config for VS Code
- `settings.json` — Repo-managed VS Code settings snapshot used for merge/setup workflows
- `global-settings.json` — Reference copy of the global VS Code settings used by the `AndrewButson.vscode-openai` extension
- `vscode-settings.json.example` — Example MCP server entry
- `setup.sh` — Install script
- `copilot-mcp.json` — Copilot's MCP bridge config (merged from `clients/copilot/`)
- `_oai-extension.json` — Inactive reference file showing the extension JSON shape and model settings
- `copilot-sampling.json` — Copilot model sampling and tool allow-list config

## Setup

```bash
./clients/vscode/setup.sh
```

## Notes

- Copilot configs were merged here since Copilot runs inside VS Code
- Project-specific PromptHub proxy settings live in `.vscode/settings.json`
- Global PromptHub proxy settings live in `clients/vscode/global-settings.json`
- `_oai-extension.json` is intentionally inactive and kept only as a format and model-settings reference
- The `AndrewButson.vscode-openai` extension uses the shared `vscode` API key for
  PromptHub proxy testing
