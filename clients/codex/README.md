# Codex

OpenAI Codex CLI. Uses **TOML** config — `generate`/`install` are not supported (raises `NotImplementedError`).

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

## CLI behavior

```bash
cd app && python -m cli generate codex
# Error: Codex uses TOML config. Edit clients/codex/config.toml manually.

cd app && python -m cli list   # Shows codex with config path
```

## Files in this directory

- `config.toml` — Reference Codex config with MCP server setup

## External references

- [Codex CLI repo](https://github.com/openai/codex)
