# Wiki Index

Master page registry for the PromptHub LLM-Wiki. Add a one-line entry for every new page under the appropriate section. Sort alphabetically within each section.

Format: bulleted list. Each entry is a wikilink (double-bracket slug) followed by an em-dash and a one-sentence summary. The example below shows the shape; the angle-bracket placeholders aren't literal syntax — replace with the real slug + summary.

```
- [[some-slug]] — Some one-sentence summary.
```

## Concepts

<!-- Distilled ideas. Agent-written after research. One idea per page. -->

- [[llm-wiki-setup]] — Why and how PromptHub maintains a wiki at `docs/wiki/`, replacing the legacy `docs/notes/` directory with a structured 4-section layout.
- [[router-auth-tokens]] — The two distinct bearer tokens (router `PH_API_TOKEN` vs LM Studio `LM_API_TOKEN`) and the `/v1`-only auth boundary that trips up local setup.

## Sources

<!-- Summarized external material (articles, docs, papers). One source per page. -->

_(empty — first source lands here.)_

## Entities

<!-- Named things: tools, services, platforms, people. One entity per page. -->

- [[llm-wiki-ops-portable]] — Claude Code skill implementing the Karpathy LLM Wiki pattern in any workspace; the engine behind this wiki.
- [[obsidian-local-rest-api]] — Obsidian community plugin exposing the vault on `127.0.0.1:27124`; as of v4.x hosts an in-process MCP server at `/mcp/`.
- [[ph-docs-hygiene-profile]] — Hygiene-skill profile auditing the wiki for orphan pages, broken wikilinks, log rotation, and `docs/notes/` coverage.
- [[schemathesis]] — Property-based OpenAPI fuzzer; quick smoke check of the router's `/openapi.json` surface via `app/schemathesis.toml`.

## Syntheses

<!-- Cross-cutting analysis combining multiple concepts/sources. -->

_(empty — first synthesis lands here.)_
