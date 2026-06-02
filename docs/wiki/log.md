# Wiki Log

Chronological change log for the PromptHub LLM-Wiki. Append-only. Rotate to `log-YYYY.md` when this file exceeds 500 entries.

> Format: `## [YYYY-MM-DDThh:mm:ss] action | subject | files`
> Actions: `create`, `ingest`, `update`, `lint`, `archive`, `delete`
> Subject: ≤300 chars summarizing what changed
> Files: comma-separated paths affected

## [2026-06-01T18:45:00] create | wiki scaffold | index.md, log.md, concepts/, sources/, entities/, syntheses/

Initialized empty wiki at `docs/wiki/` using the `llm-wiki-ops-portable` skill. Legacy notes remain at `docs/notes/` and will age out as topics are revisited and re-synthesized into the wiki. No content migration performed.

## [2026-06-01T18:55:00] create | seed pages + index population | concepts/llm-wiki-setup.md, entities/llm-wiki-ops-portable.md, entities/ph-docs-hygiene-profile.md, index.md

Seeded the first three wiki pages: a concept page explaining why the wiki exists, and two entity pages for the skill driving it and the hygiene profile auditing it. All three cross-link to each other (≥2 outbound wikilinks per page). Updated `index.md` with their entries under Concepts and Entities. Coincides with `ph-docs` hygiene profile creation and `/wiki-*` slash command setup.

## [2026-06-01T20:30:00] create | obsidian-local-rest-api entity | entities/obsidian-local-rest-api.md, index.md

First non-meta wiki page. Documents the unified Obsidian plugin (formerly two separate plugins: `obsidian-local-rest-api` for REST + `mcp-tools` for stdio MCP, merged in v4.x). Covers port 27124, bearer auth, the new `/mcp/` endpoint, keychain entries, PromptHub integration history (stale path fix + pending mcp-remote migration), and vault-scoping caveats (Scratch has it, PKB doesn't). Cross-links to two not-yet-existing pages: `[[mcp-stdio-vs-http-transport]]` (concept) and `[[mcp-remote]]` (entity) — intentional pending follow-ups that the next lint will surface as Doc3 findings.
