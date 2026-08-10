# VS Code + GitHub Copilot

Bridge client using `mcp.servers` format. VS Code settings contain many
non-MCP preferences, so `setup.sh` handles the MCP merge separately.

## Files in directory

- `mcp.json` - MCP bridge config for VS Code and the user-level symlink target
- `settings.json` - Repo-managed VS Code workspace settings snapshot
- `global-settings.json` - Reference copy of the global VS Code settings used
  by the `AndrewButson.vscode-openai` extension
- `vscode-settings.json.example` - Example MCP server entry
- `setup.sh` - Helper that explains the user-level `mcp.json` sync path
- `copilot-mcp.json` - Copilot's MCP bridge config merged from `clients/copilot/`
- `_oai-extension.json` - Inactive reference file showing the extension JSON
  shape and model settings
- `copilot-sampling.json` - Copilot model sampling tool allow-list config

## Setup

```bash
./clients/vscode/setup.sh
```

## Notes

- Copilot configs are merged because Copilot runs inside VS Code.
- Project-specific PromptHub proxy settings live in `.vscode/settings.json`.
- Global PromptHub proxy settings live in `clients/vscode/global-settings.json`.
- `_oai-extension.json` stays inactive and exists only as a format reference.
- `AndrewButson.vscode-openai` uses the shared `vscode` API key for PromptHub
  proxy testing.
