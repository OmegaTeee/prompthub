# PromptHub Wiki

Central knowledge base for architecture decisions, patterns, entities, and sources.

```
[[some-slug]] — One-sentence summary.
```

## Concepts

Distilled ideas. One per page.

- [[concepts/git-pr-workflow]] — Squash-merge workflow via `gh` CLI and non-interactive gotchas.
- [[concepts/llm-wiki-setup]] — Why and how PromptHub maintains a wiki at `docs/wiki/`.
- [[concepts/router-auth-tokens]] — Two distinct bearer tokens (`PH_API_TOKEN` vs `LM_API_TOKEN`).
- [[concepts/sqlite-query-param-guards]] — Why unvalidated GET params cause 500s in SQLite.
- [[concepts/three-track-documentation]] — Tour/Product/Setup file pattern for feature docs.

## Sources

Summarized external material.

- [[sources/secrets-management-patterns]] — Keychain/keyring patterns for storing external API keys.
- [[sources/task-tracking-conventions]] — TODO consolidation and task-tracking conventions.

## Entities

Named things: tools, services, platforms, people.

- [[entities/llm-wiki-ops-portable]] — Claude Code skill implementing Karpathy LLM Wiki pattern.
- [[entities/obsidian-local-rest-api]] — Obsidian plugin exposing vault on `127.0.0.1:27124`.
- [[entities/ph-docs-hygiene-profile]] — Profile for auditing wiki hygiene and structure.
- [[entities/schemathesis]] — Property-based OpenAPI fuzzer via `app/schemathesis.toml`.
- [[entities/keyring-integration-complete]] — Platform-native secure credential store integration.
- [[entities/mcp-remote]] — Lightweight shim for talking to a local MCP over remote transport.
- [[entities/mcp-stdio-vs-http-transport]] — Stdio vs HTTP MCP transport trade-offs.
- [[entities/session-memory-storage]] — `SessionStorage` SQLite layer with FTS5 search.

## Syntheses

Cross-cutting analysis combining concepts/sources.

- [[syntheses/middleware-architecture]] — ASGI middleware patterns distilled from enhancement review.

---
*Updated: 2026-07-06*