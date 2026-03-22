This document explains the `X-Enhance` header and related settings used by the Enhancement Middleware.

- Header: `X-Enhance` — per-request opt-in. Supported truthy values: `1`, `true`, `True`, `yes`, `YES`, `on`, `ON`.
- Setting: `auto_enhance_mcp` — when true, enhancements run automatically for MCP POST requests.
- Setting: `max_enhancement_body_size` — maximum request body size (bytes) allowed for enhancement. Requests larger than this are skipped to protect memory.
- Setting: `enhancement_slow_ms_threshold` — threshold in milliseconds above which enhancement calls are logged as "slow" for monitoring.

Notes and recommendations:

- The middleware replaces the request body for downstream handlers. Because Starlette/FastAPI do not provide a public API for body replacement, the implementation modifies private attributes. We pin `starlette` to a known compatible version and include integration tests to validate behavior.
- For production, consider enabling metrics collection and alerting on slow enhancement calls. Also consider external rate-limiting if untrusted clients may trigger high volumes of enhancements.

Example (per-request enhancement):

POST /mcp/your-server/tools/call
Headers:
- `X-Enhance: true`

Body (JSON-RPC):

{
  "jsonrpc": "2.0",
  "method": "tools.call",
  "params": { "prompt": "Summarize this text..." }
}
