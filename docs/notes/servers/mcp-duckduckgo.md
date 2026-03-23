---
title: "MCP Server Card: duckduckgo — Web Search"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, duckduckgo, search, web]
---

# duckduckgo

DuckDuckGo web search with SafeSearch and region support. Lightweight search server for general web queries — no API key required.

## Server Details

| Property | Value |
|---|---|
| Package | `ddg-mcp-search` |
| Version | 1.1.0 |
| Transport | stdio |
| Auto-start | Yes |
| Restart on failure | Yes |
| Max restarts | 3 |
| Health check | 30s |

## Tools

| Tool | Description |
|---|---|
| `search` | Search the web via DuckDuckGo |

## PromptHub Integration

**Orchestrator mapping**: Not directly mapped to any intent category. Available as a general-purpose tool when clients include it in their `SERVERS` filter.

**Client availability**:

| Client | Included |
|---|---|
| Claude Desktop | Yes |
| Claude Code | Yes |
| Raycast | Yes |
| Perplexity | No (has its own search) |
| OpenClaw | Yes |
| Open WebUI | Yes (`GATEWAY_SERVERS=...,duckduckgo`) |
| MCP Inspector | No |

## Notes

- No API key or environment variables required — uses DuckDuckGo's public search.
- Complements `context7` — duckduckgo is for general web, context7 is for library docs.
- Not included in Perplexity's `SERVERS` filter because Perplexity has native search built in.
- Single tool with simple schema — works reliably even with smaller models through minified schemas.
