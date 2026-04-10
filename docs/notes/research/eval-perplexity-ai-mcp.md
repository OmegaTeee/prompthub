---
status: parked
date: 2026-04-10
---

# @perplexity-ai/mcp-server

Official Perplexity AI MCP server providing direct API access to Perplexity's search and research models. Evaluated against `perplexity-comet-mcp` (the CDP browser bridge currently in use).

## Source

- **Package**: `@perplexity-ai/mcp-server` (npm)
- **Version evaluated**: 0.8.5
- **Requires**: `PERPLEXITY_API_KEY` environment variable (Pro account)

## What it does

Provides MCP tools for querying Perplexity's API directly — no browser needed. Supports model selection, citation retrieval, and structured search across Perplexity's index.

## How it differs from perplexity-comet

| Aspect | `@perplexity-ai/mcp-server` | `perplexity-comet-mcp` |
| --- | --- | --- |
| Transport | Direct HTTP API | CDP bridge via Comet browser |
| Authentication | API key (Pro required) | Browser session (free tier works) |
| Browser required | No | Yes (Comet must be running) |
| Search modes | API-defined models | Browser UI modes (search, research, reasoning) |
| Screenshots | No | Yes (`comet_screenshot`) |
| Tab management | No | Yes (`comet_tabs`) |
| File upload | No | Yes (`comet_upload`) |
| Latency | Lower (direct API) | Higher (browser automation) |
| Cost | Per-query API pricing | Free (uses browser session) |

## Why we're parking it

1. **`perplexity-comet` is already working well** — it's auto_start, integrated into 7 client configs, and provides richer capabilities (screenshots, tabs, file upload) that the API server doesn't have
2. **API key cost**: The direct API charges per query while the browser bridge uses your existing Perplexity session for free
3. **No urgent use case**: We don't currently need the lower latency or headless operation that the API server provides

## When to revisit

- If Perplexity deprecates web scraping / CDP access
- If you need headless Perplexity queries (CI/CD, background jobs)
- If the browser bridge becomes unreliable or too slow
- If Perplexity adds API-only features not available in the web UI

## Cleanup

Uninstalled from `mcps/package.json` in the `chore/mcps-cleanup` PR. The `PERPLEXITY_API_KEY` remains in keyring (`perplexity_api_key`) for future use. Reinstall with:

```bash
cd mcps && npm install @perplexity-ai/mcp-server
```
