---
title: "MCP Server Card: browsermcp — Chrome Extension Browser Automation"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [mcp, server, browsermcp, browser, automation, chrome-extension]
---

# browsermcp

Browser automation via Chrome extension WebSocket bridge. Drives existing Chrome tabs — supports navigation, clicking, typing, screenshots, and accessibility snapshots.

## Server Details

| Property | Value |
|---|---|
| Package | `@browsermcp/mcp` |
| Version | 0.1.3 |
| Transport | stdio |
| Auto-start | **No** (requires Chrome extension) |
| Restart on failure | No |
| Max restarts | 3 |
| Health check | 30s |

## Tools

- **Navigation**: `browser_navigate`, `browser_go_back`, `browser_go_forward`
- **Interaction**: `browser_click`, `browser_hover`, `browser_type`, `browser_press_key`, `browser_select_option`
- **Inspection**: `browser_screenshot`, `browser_snapshot` (accessibility tree)
- **Utility**: `browser_wait`, `browser_get_console_logs`

## PromptHub Integration

**Client availability**:

| Client | Included |
|---|---|
| OpenClaw | Yes (`SERVERS=...,browsermcp`) |
| All others | No |

## Comparison with chrome-devtools-mcp

| Feature | browsermcp | chrome-devtools-mcp |
|---|---|---|
| **Connection** | Chrome extension WebSocket | CDP (`--browserUrl`) |
| **Setup** | Install extension, connect | Launch browser with `--remote-debugging-port` |
| **Tab access** | Existing tabs (extension injects) | All tabs via CDP |
| **Performance tools** | No | Yes (tracing, Lighthouse, memory) |
| **Network inspection** | No | Yes |
| **Tool count** | ~12 | ~30 |
| **Best for** | Simple automation, form filling | Deep debugging, profiling, performance |

## Notes

- Lighter alternative to chrome-devtools-mcp — fewer tools, simpler setup, but limited to what the Chrome extension exposes.
- Currently only included in OpenClaw's `SERVERS` filter. Not in `GATEWAY_SERVERS` for Open WebUI.
- Manual start only — requires the BrowserMCP Chrome extension to be installed and connected.
- No environment variables or API keys required.
