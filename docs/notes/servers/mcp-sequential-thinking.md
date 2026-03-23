---
title: "MCP Server Card: sequential-thinking — Step-by-Step Reasoning"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, sequential-thinking, reasoning, planning]
---

# sequential-thinking

Step-by-step reasoning and problem solving. Provides a structured thinking tool that guides LLMs through multi-step analysis with revision and branching support.

## Server Details

| Property | Value |
|---|---|
| Package | `@modelcontextprotocol/server-sequential-thinking` |
| Version | 2025.12.18 |
| Transport | stdio |
| Auto-start | Yes |
| Restart on failure | Yes |
| Max restarts | 3 |
| Health check | 30s |

## Tools

| Tool | Description |
|---|---|
| `sequentialthinking` | Record a thought in a sequential chain, with support for revisions and branching |

## PromptHub Integration

**Orchestrator mapping**: Suggested for `code`, `documentation`, `workflow`, and `reasoning` intents — the most broadly mapped server.

**Client availability**:

| Client | Included |
|---|---|
| Claude Desktop | Yes |
| Claude Code | Yes |
| Raycast | Yes |
| Perplexity | Yes |
| OpenClaw | Yes |
| Open WebUI | Yes |
| MCP Inspector | Yes |

## Notes

- Single tool, minimal schema — negligible impact from minification.
- The most universally recommended server by the orchestrator (4 of 7 intent categories).
- Previously competed with `deepseek-reasoner` for the reasoning role; deepseek-reasoner was removed as redundant (see CHANGELOG `[Unreleased]`).
- No environment variables or API keys required.
