# MCP routing

This guide explains how coding agents should think about PromptHub's MCP routing behavior, server sharing, transport assumptions, and fallback logic.

## Core principle

PromptHub is the source of truth for shared MCP server definitions and centralized client configuration.
Changes to routing should strengthen consistency across clients rather than create one-off routing behavior for a single tool.

## Routing expectations

- Prefer shared routing abstractions over client-specific branching.
- Keep server identity stable across clients where possible.
- Use consistent naming for server labels, transport terms, and environment variables.
- Preserve compatibility with supported clients unless a task explicitly authorizes a breaking change.
- If a new client needs special handling, isolate it cleanly and document why.

## Server sharing

When adding or changing a server definition:

1. Check whether an existing shared definition or adapter already covers the need.
2. Prefer extending shared server metadata rather than duplicating server definitions per client.
3. Keep any client-specific projection logic thin and easy to inspect.
4. Update docs and examples when a server's shared behavior changes.

## Transport assumptions

Before changing transport behavior, read relevant architecture docs and ADRs.
In particular, review:

- `docs/architecture/ADR-001-stdio-transport.md`
- `docs/architecture/mcp-transport-adapters.md`
- `docs/architecture/ADR-002-circuit-breaker.md`
- `docs/architecture/ADR-007-cloud-fallback.md`

## Fallback logic

Fallback behavior should be explicit, predictable, and documented.
Do not hide meaningful routing or provider behavior behind silent special cases.

When changing fallback behavior:

- Validate the happy path first.
- Validate at least one timeout, failure, or degraded-path scenario.
- Record any client-visible behavior change in docs.
- Prefer centralized fallback policy over per-client ad hoc logic.

## Local model assumptions

For local-model workflows, assume LM Studio is the default local LLM backend unless the task states otherwise.
If routing or client logic depends on model-provider behavior, document the assumption clearly and avoid hardcoding unnecessary provider-specific behavior.

## Change checklist

Before finalizing routing work, confirm:

- Shared server definitions remain the source of truth.
- Naming is still consistent across clients.
- Transport assumptions still match the architecture docs.
- Fallback behavior was validated, not assumed.
- Affected docs and config examples were updated.

## Output expectations

In the final summary for routing-related work, include:

- What routing behavior changed.
- Which clients were affected.
- Which fallback or error scenarios were checked.
- Any compatibility or migration risk.
