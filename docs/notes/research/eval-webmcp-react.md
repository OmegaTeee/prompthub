---
status: evaluated
date: 2026-04-10
---

# WebMCP React (webmcp-react)

React hooks library for exposing web app functionality as MCP tools via a browser extension. Evaluated as a potential bridge between web UIs and PromptHub's MCP server ecosystem.

## Source

- **Repository**: https://github.com/MCPCat/webmcp-react
- **Author**: Kashish Hora, Naseem Alnaji
- **License**: MIT
- **Version evaluated**: 0.1.0 (commit `00b5670` — AbortSignal-based tool unregistration, Chrome 148)

## What it does

Provides `useTool()` and `useToolGroup()` React hooks that register web app functions as MCP tools. A companion Chrome extension (`webmcp-bridge-extension`) bridges the browser to MCP clients via the proposed `navigator.modelContext` W3C API.

Key features:
- Transport-agnostic (works with any MCP client that supports the bridge extension)
- SSR-safe, React Strict Mode safe
- Zod schema → JSON Schema conversion for tool input validation
- Includes playground and Next.js example apps

## Why we looked at it

PromptHub's `browsermcp` server (`@browsermcp/mcp`) drives Chrome tabs via a browser extension WebSocket bridge. WebMCP React takes the opposite approach — the *web app itself* registers tools, rather than an external driver controlling the browser. This could enable tighter integration where PromptHub-connected LLMs call functions inside running web apps (e.g., triggering Obsidian vault actions from the web UI, or interacting with Open WebUI's interface).

## Decision

**Not adopted.** The library targets a use case we don't currently have (web apps exposing tools to LLMs). PromptHub's architecture flows the other way — LLMs call MCP servers, which then interact with apps. If a future client is a web app that needs to expose its own tools, this library would be worth revisiting.

## Cleanup

The cloned repo was at `mcps/web/` (nested git repo). Deleted in the `chore/mcps-cleanup` PR. The `.gitignore` entry `mcps/web/` was added in PR #7 to prevent accidental re-tracking.
