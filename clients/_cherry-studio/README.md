# Cherry Studio

Cherry Studio is a **dual-mode** PromptHub client:

1. **MCP bridge** (stdio) — tools via `mcpServers` config
2. **HTTP provider** — chat completions via `/v1/responses` endpoint

## MCP Bridge Setup

Cherry Studio stores its MCP config in Electron's LevelDB (`Local Storage`), not in an external file. Configuration is done through the GUI.

### Quick setup

1. Open `mcp-servers-example.json` in this directory.
2. In Cherry Studio, go to **Settings > MCP Servers > Edit JSON**
3. Paste the generated JSON into the editor, then click **OK**

### GUI fields (General tab)

| Field | Value |
|-------|-------|
| Name | `prompthub-bridge` |
| Description | `local router` |
| Type | Standard Input/Output (stdio) |
| Command | `node` |
| Arguments | `/Users/<you>/prompthub/mcps/prompthub-bridge.js` |
| Environment Variables | See below |
| Long Running Mode | ON |
| Timeout | `60` s |

### Environment variables

```
PROMPTHUB_URL=http://127.0.0.1:9090
AUTHORIZATION=Bearer sk-prompthub-cherry-001
CLIENT_NAME=cherry-studio
SERVERS=memory,context7,sequential-thinking,desktop-commander,perplexity-comet
```

### Advanced Settings (optional)

| Field | Value |
|-------|-------|
| Provider | `OmegaTeee` |
| Provider URL | (blank) |

## HTTP Provider Setup

Cherry Studio also connects as an OpenAI-compatible provider for chat. Add a provider in **Settings > Model Service > Add Provider**:

| Field | Value |
|-------|-------|
| Name | `PromptHub Router` |
| Type | OpenAI Response |
| API Host | `http://127.0.0.1:9090` |
| API Key | `sk-prompthub-cherry-001` |

After adding, click **Manage** to discover available models from the router.

## Config location

Cherry Studio persists all settings (providers, MCP servers, assistants, memory) in:

```
~/Library/Application Support/CherryStudio/Local Storage/leveldb/
```

This is Electron's LevelDB — not a user-editable file. Use the GUI or the **Edit JSON** dialog for changes.

The `config.json` in that directory only contains Electron app preferences (theme, tray, hardware acceleration) — not provider or MCP settings.

## Files in this directory

- `cherry-studio-llm.txt` — LLM knowledge file (provider, MCP, agent, knowledge base docs)
- `mcp-servers-example.json` — Reference JSON for the Edit JSON dialog
- `assets/` — Screenshots of the MCP config GUI tabs (6 images)

## External references

- [Cherry Studio repo](https://github.com/kangfenmao/cherry-studio)
- [Cherry Studio docs (English)](https://github.com/CherryHQ/cherry-studio-docs/tree/main/i18n/english)
- [MCP usage tutorial](https://github.com/CherryHQ/cherry-studio-docs/blob/main/i18n/english/advanced-basic/mcp/config.md)
- [Custom provider setup](https://github.com/CherryHQ/cherry-studio-docs/blob/main/i18n/english/pre-basic/providers/zi-ding-yi-fu-wu-shang.md)
- [Cherry Agent tutorial](https://github.com/CherryHQ/cherry-studio-docs/blob/main/i18n/english/advanced-basic/agent.md)
- [GitHub discussions](https://github.com/CherryHQ/cherry-studio/discussions)
