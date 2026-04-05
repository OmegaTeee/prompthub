# VS Code

Bridge client using `mcp.servers` format (nested under `mcp` key). Merge install — VS Code settings contain many non-MCP preferences.

## Config path

```
~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json
```

Note: This path is for the Roo Cline extension's MCP settings. Other extensions may use different paths.

## Quick setup

```bash
cd app && python -m cli generate vscode
cd app && python -m cli install vscode
```

## Files in this directory

- `settings.json` — Symlink to VS Code `settings.json` (shared system file)

## External references

- [VS Code MCP support](https://code.visualstudio.com/docs)
