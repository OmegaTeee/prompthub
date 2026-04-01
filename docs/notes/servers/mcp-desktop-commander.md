---
title: "MCP Server Card: desktop-commander — File Operations & Terminal"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, desktop-commander, filesystem, terminal]
---

# desktop-commander

File operations and terminal commands. The most tool-rich server in the roster — provides filesystem access, process management, file editing, and search capabilities.

## Server Details

| Property | Value |
|---|---|
| Package | `@wonderwhy-er/desktop-commander` |
| Version | 0.2.35 |
| Transport | stdio |
| Auto-start | Yes |
| Restart on failure | Yes |
| Max restarts | 3 |
| Health check | 30s |

## Environment Variables

| Variable | Value | Purpose |
|---|---|---|
| `CLIENT_IP_ENCRYPTION_KEY` | `3765aa62...` | Encrypts client IP in audit logs |

## Tools (26)

Core categories:
- **File I/O**: `read_file`, `read_multiple_files`, `write_file`, `move_file`, `create_directory`, `get_file_info`, `list_directory`
- **Editing**: `edit_block` (surgical block replacement)
- **Terminal**: `start_process`, `interact_with_process`, `read_process_output`, `kill_process`, `force_terminate`, `list_processes`, `list_sessions`
- **Search**: `start_search`, `get_more_search_results`, `list_searches`, `stop_search`
- **Config**: `get_config`, `set_config_value`, `get_usage_stats`, `get_recent_tool_calls`, `get_prompts`
- **Output**: `write_pdf`
- **Feedback**: `give_feedback_to_desktop_commander`

## PromptHub Integration

**Orchestrator mapping**: Suggested for `code`, `documentation`, and `workflow` intents.

**Client availability**:

| Client | Included |
|---|---|
| Claude Desktop | Yes |
| Claude Code | Yes |
| Raycast | Yes |
| Perplexity | Yes |
| OpenClaw | Yes |
| Open WebUI | No (excluded from `GATEWAY_SERVERS`) |
| MCP Inspector | Yes |

**Schema minification impact**: This server benefits most from minification — 26 tools with verbose schemas reduce by ~76% (56,910 → 13,881 bytes).

## Notes

- Largest tool count of any server. Consider filtering with `EXCLUDE_TOOLS` for smaller models.
- Excluded from Open WebUI's `GATEWAY_SERVERS` to keep tool count manageable for local models.
- The `edit_block` tool is the primary mechanism for code editing through MCP clients.
