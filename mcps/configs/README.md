# Desktop MCP Configurations

Configuration files for connecting desktop clients to PromptHub via the MCP bridge.

## Quick Start — CLI

The CLI generates path-safe configs from `app/`. All paths are resolved to absolute — no `~`, `${HOME}`, or `$HOME` that Node.js can't expand.

```bash
cd app

# Generate config for a client (prints JSON to stdout)
python -m cli generate claude-desktop
python -m cli generate raycast
python -m cli generate vscode

# With server filter and tool exclusions
python -m cli generate claude-desktop \
  --servers "context7,desktop-commander,sequential-thinking" \
  --exclude-tools "duckduckgo,perplexity"

# Validate an installed config for common issues
python -m cli validate claude-desktop

# Compare installed config vs. what the CLI would generate
python -m cli diff claude-desktop

# Install into the client's active config file (merges, creates backup)
python -m cli install claude-desktop --dry-run   # Preview first
python -m cli install claude-desktop              # Write for real

# Show all supported clients and their config file locations
python -m cli list

# Full stack health check (node, bridge, router, servers, config)
python -m cli diagnose
```

## Config Files

Source-of-truth MCP bridge configs. Each tells a client how to connect to PromptHub via the stdio bridge. Client apps read these through symlinks from their expected config paths. Client application settings live in [`clients/`](../../clients/) at the project root.

| File | Client | Symlinked from | Format |
|------|--------|----------------|--------|
| `claude-desktop.json` | Claude Desktop | `~/Library/.../Claude/claude_desktop_config.json` | `mcpServers` |
| `claude-code.json` | Claude Code | `.mcp.json` (project root) | `mcpServers` |
| `copilot.json` | GitHub Copilot | `~/Library/.../Code/User/mcp.json` | `servers` |
| `raycast-mcp.json` | Raycast | `~/.config/raycast/mcp.json` | `mcpServers` |
| `openclaw-mcps.json` | OpenClaw | `~/.openclaw/mcp-config.json` | `mcpServers` |
| `perplexity.json` | Perplexity | — | Bare entry (`useBuiltInNode: true`) |
| `mcp-inspector.json` | MCP Inspector | — | `mcpServers` (testing only) |

### Symlink Convention

```
mcps/configs/claude-desktop.json                          ← real file (git-tracked)
~/Library/.../Claude/claude_desktop_config.json           ← symlink → ~/prompthub/mcps/configs/claude-desktop.json
```

**Source in the project, symlink at the client location.** Edit configs here; clients read through the symlink.

## How It Works

All clients connect through one Node.js bridge (`mcps/prompthub-bridge.js`) that aggregates PromptHub's MCP servers into a single stdio interface.

```
Desktop Client  ──stdio──►  prompthub-bridge.js  ──HTTP──►  PromptHub Router (:9090)
                                                                    │
                                                              ┌─────┴─────┐
                                                              ▼           ▼
                                                          context7   desktop-commander
                                                          sequential-thinking   memory
                                                          ...        ...
```

### Bridge Environment Variables

The bridge reads these env vars from the config's `env` block:

| Variable | Required | Description |
|----------|----------|-------------|
| `PROMPTHUB_URL` | Yes | Router URL. Use `http://127.0.0.1:9090`, not `localhost` |
| `CLIENT_NAME` | Yes | Client identifier (e.g. `claude-desktop`, `raycast`) |
| `AUTHORIZATION` | No | Bearer token from `app/configs/api-keys.json` |
| `SERVERS` | No | Comma-separated server filter (e.g. `context7,desktop-commander`) |
| `EXCLUDE_TOOLS` | No | Comma-separated prefixed tool names to hide |

### Path Safety

Node.js `child_process.spawn()` does NOT expand shell variables. These paths will fail:

```
"args": ["${HOME}/prompthub/mcps/prompthub-bridge.js"]   ← broken
"args": ["~/prompthub/mcps/prompthub-bridge.js"]         ← broken
"command": "~/prompthub/mcps/prompthub-bridge.js"        ← broken
```

Always use absolute paths:

```
"args": ["/Users/visualval/prompthub/mcps/prompthub-bridge.js"]  ← correct
```

The CLI enforces this automatically — `python -m cli generate` will never produce broken paths.

## Validator Checks

`python -m cli validate <client>` catches:

- `~` or `${HOME}` or `$HOME` in command or args (error)
- Relative `.js` paths in args (error)
- Legacy `AGENTHUB_URL` env var (error — should be `PROMPTHUB_URL`)
- `localhost` in `PROMPTHUB_URL` (warning — use `127.0.0.1`)
- Missing bridge file at resolved path (warning)

## Diagnostics

`python -m cli diagnose` checks the full stack:

```
  [PASS] Node.js: node v25.6.1
  [PASS] Bridge file: Found (6551 bytes)
  [PASS] Router: Healthy (status=healthy)
  [PASS] Servers: 6 running: context7, desktop-commander, ...
  [PASS] Installed config: Valid
```

## Client-Specific Notes

### Claude Desktop

Config path: `~/Library/Application Support/Claude/claude_desktop_config.json`

The `install` command merges only `mcpServers.prompthub` — it preserves your `preferences` section and any other MCP servers you've configured.

### Raycast

Config path: `~/.config/raycast/mcp.json`

Uses standard `mcpServers` format. Generated configs include the bearer token from `api-keys.json`.

### VS Code

Config path varies by extension. The CLI generates `{"mcp": {"servers": {...}}}` format (VS Code's MCP schema is different from Claude Desktop).

### Perplexity

Uses a bare entry format with `useBuiltInNode: true`. The CLI's `generate` command produces `mcpServers`-wrapped output; for Perplexity's format, use the config in this directory directly.

## MCP Inspector

For testing the bridge in isolation:

```bash
cd mcps && npx @anthropic/mcp-inspector node prompthub-bridge.js
```

Access at [http://localhost:6274](http://localhost:6274) to browse tools, test calls, and inspect JSON-RPC traffic.
