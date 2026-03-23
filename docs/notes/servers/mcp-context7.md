---
title: "MCP Server Card: context7 — Library Documentation Fetcher"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, context7, documentation, libraries]
---

# context7

Fetches up-to-date documentation and code examples for any library. Resolves library identifiers and retrieves relevant docs on demand — replaces the need to manually search docs sites.

## Server Details

| Property | Value |
|---|---|
| Package | `@upstash/context7-mcp` |
| Version | 2.1.1 |
| Transport | stdio |
| Auto-start | Yes |
| Restart on failure | Yes |
| Max restarts | 3 |
| Health check | 30s |

## Tools

| Tool | Description |
|---|---|
| `resolve-library-id` | Resolve a library name to a Context7-compatible library ID |
| `get-library-docs` | Fetch documentation for a resolved library ID |

## PromptHub Integration

**Orchestrator mapping**: Suggested for `code`, `documentation`, and `search` intents.

**Client availability**:

| Client | Included | Via |
|---|---|---|
| Claude Desktop | Yes | Bridge `SERVERS` (default: all) |
| Claude Code | Yes | Bridge `SERVERS` (default: all) |
| Raycast | Yes | `SERVERS=...,context7` |
| Perplexity | Yes | `SERVERS=...,context7` |
| OpenClaw | Yes | `SERVERS=...,context7` |
| Open WebUI | Yes | `GATEWAY_SERVERS=context7,...` |
| MCP Inspector | Yes | `SERVERS=context7,...` |

**Tool registry**: Cached in SQLite (`tool_registry.db`) with 24h TTL. Served from cache on repeat `tools/list` requests.

## Notes

- No environment variables or API keys required — works out of the box.
- One of the most universally useful servers — included in every client's `SERVERS` filter.
- Complements `duckduckgo` (web search) — context7 is for library docs, duckduckgo is for general web.
