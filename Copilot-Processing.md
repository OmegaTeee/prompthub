# Copilot Processing

## User request
- Normalize documentation references so the Qwen3 family is described as "Qwen3" instead of variant labels such as "Qwen3 Instruct" or "Qwen3 Thinking" when the prose is describing the family rather than a specific runtime model ID.
- Keep exact runtime model IDs unchanged where they are operationally meaningful (for example `qwen3-4b-instruct-2507`, `qwen3-4b-thinking-2507`, and `qwen-3.8b-distill`).
- Preserve the current local setup note: the MCP health monitor and tool compression pipeline use `qwen-3.8b-distill`.

## Plan
1. Review active documentation pages that describe the model family in narrative language.
2. Replace generic family labels with plain "Qwen3" or "Qwen3 thinking variant" while leaving exact model IDs and config values alone.
3. Validate with a focused search to confirm the remaining references are runtime identifiers or intentionally specific config values.
