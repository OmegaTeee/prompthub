# Codex

OpenAI Codex CLI. Uses **TOML** config and is maintained from the tracked
example in this directory rather than a generated installer.

## Config path

```
~/.codex/config.toml
```

## Setup

Edit the config file manually. Reference config:

```toml
[mcp_servers.prompthub]
command = "node"
args = ["/Users/<you>/prompthub/mcps/prompthub-bridge.js"]
cwd = "~/"
enabled = true

[mcp_servers.prompthub.env]
AUTHORIZATION = "Bearer sk-prompthub-codex-001"
CLIENT_NAME = "codex"
PROMPTHUB_URL = "http://127.0.0.1:9090"
SERVERS = "memory,sequential-thinking,desktop-commander,perplexity-comet,context7"
```

## Setup workflow

Copy or merge `config.toml` into `~/.codex/config.toml`, then adjust local
paths and tokens as needed.

## Files in this directory

- `config.toml` — Reference Codex config with MCP server setup

## External references

- [Codex CLI repo](https://github.com/openai/codex)
