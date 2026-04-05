# VS Code + GitHub Copilot

Bridge client using `mcp.servers` format. VS Code settings contain many non-MCP preferences — setup.sh handles the merge.

## Files in this directory

- `mcp.json` — MCP bridge config for VS Code
- `settings.json` — Symlink to VS Code `settings.json` (shared system file)
- `vscode-settings.json.example` — Example MCP server entry
- `setup.sh` — Install script
- `copilot-mcp.json` — Copilot's MCP bridge config (merged from `clients/copilot/`)
- `copilot-oai-extension-example.json` — OpenAI extension compatibility example
- `copilot-sampling.json` — Copilot model sampling and tool allow-list config

## Setup

```bash
./clients/vscode/setup.sh
```

## Notes

- Copilot configs were merged here since Copilot runs inside VS Code
- Copilot's API key in `api-keys.json` is still `client_name: "copilot"`
