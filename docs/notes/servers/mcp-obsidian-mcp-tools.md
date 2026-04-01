---
title: "MCP Server Card: obsidian-mcp-tools — Obsidian Vault Operations"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, obsidian, vault, knowledge-management]
---

# obsidian-mcp-tools

Obsidian vault operations via the MCP Tools plugin. Reads, writes, and searches notes in the Obsidian vault through a local REST API.

## Server Details

| Property | Value |
|---|---|
| Package | `obsidian-mcp-tools` |
| Version | (Obsidian plugin binary) |
| Transport | stdio |
| Command | `/Users/visualval/Vault/.obsidian/plugins/mcp-tools/bin/mcp-server` |
| Auto-start | Yes |
| Restart on failure | Yes |
| Max restarts | 3 |
| Health check | 30s |

## Environment Variables

| Variable | Value | Purpose |
|---|---|---|
| `OBSIDIAN_API_KEY` | keyring (`prompthub/obsidian_api_key`) | Auth for Obsidian REST API |
| `OBSIDIAN_HOST` | `https://127.0.0.1` | Obsidian REST plugin host |
| `OBSIDIAN_PORT` | `27124` | Obsidian REST plugin port |

## PromptHub Integration

**Orchestrator mapping**: Not directly mapped. Available via `GATEWAY_SERVERS` for HTTP clients and through bridge `SERVERS` filter for stdio clients that include it.

**Client availability**:

| Client | Included |
|---|---|
| Claude Desktop | Yes |
| Claude Code | Yes |
| Raycast | No |
| Perplexity | No |
| OpenClaw | No |
| Open WebUI | Yes (`GATEWAY_SERVERS=...,obsidian-mcp-tools`) |
| MCP Inspector | No |

## Notes

- **Requires Obsidian running** with the MCP Tools plugin active and REST API enabled on port 27124.
- API key stored in macOS Keychain via `keyring` — not in config files. The `"source": "keyring"` entry in `mcp-servers.json` triggers `KeyringManager` to resolve the key at server start.
- Unlike other servers that run from `node_modules`, this runs a binary from the Obsidian plugin directory.
- User guides live in the Obsidian vault at `~/Vault/PromptHub/`.
