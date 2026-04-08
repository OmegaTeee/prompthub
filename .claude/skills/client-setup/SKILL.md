---
name: client-setup
description: >
  Interactive wizard for setting up or updating PromptHub client configurations.
  Walks through client name, strategy, config paths, API key, and enhancement rules.
  Trigger on: "set up a client", "add a new client", "configure client",
  "wire up client", "/client-setup".
---

# Client Setup — Interactive Configuration Wizard

Guide the user through setting up a new PromptHub client or updating an existing one. Each client follows the same template but may differ in strategy, config path, API key, and enhancement rules.

## When to Use

- Adding a new AI client to PromptHub
- Wiring up a placeholder (`_` prefixed) client to make it active
- Reviewing/fixing an existing client's configuration
- User says "set up client", "add client", "wire up", or "configure"

## Phase 1: Gather Client Info

Use `AskUserQuestion` to collect the following. Pre-fill defaults where possible by reading existing configs.

### Question 1: Client identity

Ask:
- **Client name** — The identifier used across configs (e.g., `cherry-studio`, `zed`). Must be lowercase, hyphenated.
- **Display name** — Human-readable name for READMEs (e.g., `Cherry Studio`, `Zed`)

Check if `clients/<name>/` or `clients/_<name>/` already exists. If so, inform the user and offer to update the existing config.

### Question 2: Setup strategy

Ask which strategy this client uses:

| Strategy | When to use | What setup.sh does |
|---|---|---|
| **symlink** | App reads a standalone JSON config file | Creates symlink from app config path to repo file |
| **manual** | App uses shared settings (JSONC, Electron dialogs) | Prints paste instructions |
| **copy** | App reads from project root (like Claude Code) | Copies config file |

### Question 3: Config paths

Ask:
- **APP_CONFIG** — Where does the app expect its config file? (e.g., `~/.lmstudio/mcp.json`, `~/Library/Application Support/Claude/...`)
- **CONFIG_FILE** — Which file in the client directory to link (default: `mcp.json`)

For `manual` strategy, APP_CONFIG is informational (shown in paste instructions).

### Question 4: MCP bridge settings

Ask:
- **SERVERS** — Which MCP servers should this client see? Default: `memory,context7,sequential-thinking,desktop-commander,perplexity-comet`
- **EXCLUDE_TOOLS** — Any servers to hide? (e.g., Claude Desktop excludes `duckduckgo,perplexity-comet`)

### Question 5: API key and enhancement

Ask:
- **Create API key?** — Should we add a bearer token to `app/configs/api-keys.json`? Token format: `sk-prompthub-<name>-001`
- **Enhancement enabled?** — Should prompts be rewritten before reaching the model? (`enhance: true/false`)
- **Create enhancement rule?** — Should we add a client-specific system prompt to `app/configs/enhancement-rules.json`?
- **Privacy level** — `local_only` (default), `free_ok`, or `any`

## Phase 2: Generate Files

Based on the answers, create or update the following files. Use the templates from `clients/default/` as the starting point.

### 2a. Client directory

If the directory doesn't exist, create it:
```
clients/<name>/
├── mcp.json       # MCP bridge config
├── setup.sh       # Install script
├── uninstall.sh   # Reverse script
└── README.md      # Client-specific notes
```

If a `_<name>/` directory exists (placeholder), rename it to remove the prefix:
```bash
git mv clients/_<name> clients/<name>
```

### 2b. mcp.json

Generate from this template, filling in the collected values:

```json
{
  "mcpServers": {
    "prompthub-bridge": {
      "command": "node",
      "args": ["~/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "AUTHORIZATION": "Bearer sk-prompthub-<name>-001",
        "CLIENT_NAME": "<name>",
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "SERVERS": "<servers>"
      }
    }
  }
}
```

Note: Some apps (like Claude Desktop) may need additional top-level keys (e.g., `preferences`). Ask the user if there are app-specific settings to include.

### 2c. setup.sh and uninstall.sh

Copy from `clients/default/setup.sh` and `clients/default/uninstall.sh`. Update the three variables at the top:
- `CLIENT_NAME`
- `CONFIG_FILE`
- `APP_CONFIG`

For `manual` strategy, replace the symlink logic with paste instructions (see `clients/_zed/setup.sh` for pattern).

Make both scripts executable: `chmod +x setup.sh uninstall.sh`

### 2d. README.md

Generate a brief README:

```markdown
# <Display Name>

<One sentence about this client's connection to PromptHub.>

## Files

- `mcp.json` — MCP bridge config
- `setup.sh` — Install script
- `uninstall.sh` — Reverse script

## Setup

\`\`\`bash
./clients/<name>/setup.sh
\`\`\`
```

### 2e. API key (if requested)

Add to `app/configs/api-keys.json` under `.keys`:

```json
"sk-prompthub-<name>-001": {
  "client_name": "<name>",
  "description": "<Display Name>",
  "enhance": <true|false>
}
```

### 2f. Enhancement rule (if requested)

Add to `app/configs/enhancement-rules.json` under `.clients`:

```json
"<name>": {
  "model": "qwen3-4b-instruct-2507",
  "system_prompt": "<ask user for system prompt or suggest a default based on client type>",
  "temperature": 0.3,
  "max_tokens": 500,
  "privacy_level": "<local_only|free_ok|any>"
}
```

## Phase 3: Verify

After generating files:

1. Read back each generated file and confirm it looks correct
2. If `setup.sh` uses symlink strategy, offer to run it: `./clients/<name>/setup.sh`
3. Check that the API key (if created) is valid JSON
4. Check that the enhancement rule (if created) is valid JSON
5. Show a summary of what was created/modified

## Phase 4: Update References

Update these files to reflect the new client:

- `AGENTS.md` — Add row to supported clients table
- `llm.txt` — Update client count
- `clients/README.md` — Add entry if it has a client listing

## Phase 5: Client llm.txt (deferred)

After the client is wired and working, create a `<name>-llm.txt` knowledge file in the client directory. This is a separate task — do not block setup on it.

Remind the user:

> "Your client is set up. When you're ready, find the getting-started guide or official docs for **<Display Name>** and we can create a `<name>-llm.txt` knowledge file. This helps LLM agents understand the client's config format, MCP support, and quirks. Existing examples: `clients/_cherry-studio/cherry-studio-llm.txt`, `clients/_zed/zed-llm.txt`, `clients/_jetbrains/jetbrains-llm.txt`."

The llm.txt file should cover:
- How the client discovers/loads MCP configs (file path, format, UI dialog)
- Supported MCP transport (stdio, HTTP, SSE)
- Any client-specific quirks (JSONC format, Electron LevelDB, environment variables)
- Links to official docs or getting-started guides

## Guidelines

- Always use `~/prompthub` in scripts (not `~/.local/share/prompthub`) per project convention
- Bearer token format: `sk-prompthub-<name>-001`
- Default enhancement model: `qwen3-4b-instruct-2507`
- Default SERVERS: `memory,context7,sequential-thinking,desktop-commander,perplexity-comet`
- Never hardcode absolute paths with `/Users/<username>` — use `$HOME` or `~`
- Placeholder clients use `_` prefix; remove prefix when activating
