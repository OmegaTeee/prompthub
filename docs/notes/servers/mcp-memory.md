---
title: "MCP Server Card: memory — Knowledge Graph Persistence"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, memory, knowledge-graph, sessions]
---

# memory

Cross-session context persistence via a knowledge graph. Enables LLMs to store and recall facts, entities, and relationships across conversations.

## Server Details

| Property | Value |
|---|---|
| Package | `@modelcontextprotocol/server-memory` |
| Version | 2026.1.26 |
| Transport | stdio |
| Auto-start | Yes |
| Restart on failure | Yes |
| Max restarts | 3 |
| Health check | 30s |

## Tools

Knowledge graph operations — create/read/update/delete entities, relations, and observations.

## PromptHub Integration

**Orchestrator mapping**: Suggested exclusively for `memory` intent.

**Client availability**:

| Client | Included |
|---|---|
| Claude Desktop | Yes |
| Claude Code | Yes |
| Raycast | No |
| Perplexity | No |
| OpenClaw | No |
| Open WebUI | Yes (`GATEWAY_SERVERS=...,memory`) |
| MCP Inspector | No |

**Dual memory system**: PromptHub has its own SQLite-backed session memory (`router/memory/`) that is the source of truth. The MCP Memory server is an optional sync target — `MemoryMCPClient` in `router/memory/mcp_client.py` can push facts to it for cross-tool persistence.

## Notes

- Not included in most client `SERVERS` filters — memory operations are typically handled by PromptHub's internal session system rather than exposed as client tools.
- Included in Open WebUI's `GATEWAY_SERVERS` for direct knowledge graph access from chat.
- No environment variables or API keys required.
