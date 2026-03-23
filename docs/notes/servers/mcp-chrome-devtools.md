---
title: "MCP Server Card: chrome-devtools-mcp — Browser Debugging & Automation"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, chrome-devtools, cdp, debugging, profiling]
---

# chrome-devtools-mcp

Chrome DevTools Protocol debugging, profiling, performance analysis, network inspection, and browser automation. Connects to a running browser via CDP.

## Server Details

| Property | Value |
|---|---|
| Package | `chrome-devtools-mcp` |
| Version | 0.20.3 |
| Transport | stdio |
| Auto-start | **No** (requires browser with remote debugging) |
| Restart on failure | No |
| Max restarts | 3 |
| Health check | 30s |

## Arguments

| Argument | Value | Purpose |
|---|---|---|
| `--browserUrl` | `http://127.0.0.1:9222` | CDP endpoint of the running browser |
| `--usageStatistics` | `false` | Disable Google telemetry |

## Tools (30+)

Core categories:
- **Navigation**: `navigate_page`, `new_page`, `close_page`, `select_page`, `list_pages`
- **Interaction**: `click`, `hover`, `fill`, `fill_form`, `type_text`, `press_key`, `drag`, `upload_file`
- **Inspection**: `take_screenshot`, `take_snapshot`, `take_memory_snapshot`
- **Network**: `list_network_requests`, `get_network_request`
- **Console**: `list_console_messages`, `get_console_message`
- **Performance**: `performance_start_trace`, `performance_stop_trace`, `performance_analyze_insight`, `lighthouse_audit`
- **Script**: `evaluate_script`
- **Dialog**: `handle_dialog`, `wait_for`
- **Emulation**: `emulate`, `resize_page`

## PromptHub Integration

**Client availability**: Not included in any client's default `SERVERS` filter. Must be started manually (`POST /servers/chrome-devtools-mcp/start`) when a browser with CDP is running.

## Notes

- **Requires a browser launched with remote debugging**: e.g., `open -a "Google Chrome" --args --remote-debugging-port=9222`. The user uses Comet (Perplexity browser) — the `--browserUrl` should point to Comet's CDP port.
- Largest tool count tied with desktop-commander (~30 tools). Schema minification is important for keeping context manageable.
- Manual start only — auto_start is false because the browser may not be running.
- Google telemetry explicitly disabled via `--usageStatistics false`.
