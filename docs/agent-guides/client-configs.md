# Client configs

PromptHub does not ship per-client config files or setup scripts. Every MCP client uses the same bridge entry, pasted into that client's own MCP config. The full pattern and per-client examples are in [getting-started.md](../guides/getting-started.md#connecting-clients).

## Rules

- The bridge entry is identical for every client: `command: node`, `args: [<repo>/mcps/prompthub-bridge.js]`, env `PROMPTHUB_URL=http://127.0.0.1:9090` and `CLIENT_NAME=<name>`.
- Only the container differs: Claude Code uses `.mcp.json` (key `mcpServers`), VS Code uses `.vscode/mcp.json` (key `servers`), Codex uses TOML in `~/.codex/config.toml`.
- `CLIENT_NAME` must match a key in `app/configs/enhancement-rules.json`.
- Per-client behavior (model profile, tool disclosure, privacy) is resolved server-side from that file via `GET /clients/{name}/model-profile` and `GET /clients/{name}/tool-profile`. Change the rules file, not the client config.
- Keep client-side differences thin: do not duplicate server definitions, models, or tool filters in client configs unless pinning for debugging (`TOOL_DISCLOSURE`, `TIER1_SERVERS`).
- Local-model assumptions default to LM Studio unless the task says otherwise.

## When changing client-facing behavior

Update [getting-started.md](../guides/getting-started.md), `app/configs/enhancement-rules.json`, and [config-locations.md](config-locations.md) together, and say in the final summary which clients are affected.
