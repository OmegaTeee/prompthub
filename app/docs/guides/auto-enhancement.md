# Automatic Prompt Enhancement

This guide explains the optional automatic prompt enhancement feature and how to opt-in per-request.

Overview

- AgentHub can enhance prompts using the configured Ollama/OpenAI-compatible service before forwarding JSON-RPC requests to MCP servers.

- Enhancement is controlled by settings and request headers and honors per-client rules defined in `configs/enhancement-rules.json`.

How to enable

- Global (server-side): set `auto_enhance_mcp = true` in `router/config/settings.py` (or via environment variable).

- Per-request (opt-in): include the header `X-Enhance: true` on the request to `/mcp/{server}/{path}`.

Behavior

- The middleware looks for common prompt-like fields in the JSON-RPC `params` object (e.g., `prompt`, `input`, `message`, `text`, or nested `arguments.prompt`).

- If an enhancement is performed, the middleware replaces the prompt text in the request body before forwarding.

- If the enhancement service is unavailable, the middleware gracefully forwards the original prompt.

Headers and overrides

- `X-Enhance`: set to `true`, `1`, `yes`, or `on` to opt-in per-request.

- `X-Client-Name`: used to select per-client enhancement rules from `configs/enhancement-rules.json`.

Notes

- Per-client `enabled` flags in `configs/enhancement-rules.json` still apply — if a client rule disables enhancement, the middleware will not enhance.

- The enhancement pipeline uses caching and a circuit breaker; see `router/enhancement/service.py` for details.

Example curl

```bash
curl -s -X POST "http://localhost:9090/mcp/context7/tools/call" \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: claude-desktop" \
  -H "X-Enhance: true" \
  -d '{"jsonrpc":"2.0","method":"tools.call","params":{"prompt":"Summarize this repo"}}'
```
