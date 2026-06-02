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

## [2026-06-02T03:30:00] create | router-auth-tokens + schemathesis | concepts/router-auth-tokens.md, entities/schemathesis.md, index.md

Added two cross-linked pages to reduce recurring env-var/token friction. `router-auth-tokens` (concept) documents the two distinct bearers — router `PH_API_TOKEN` (`sk-prompthub-*`) vs LM Studio `LM_API_TOKEN` (`sk-lm-*`) — the `/v1`-only auth boundary, the `:9090` vs `:1234` base-URL pitfall, and the `default` test key. `schemathesis` (entity) covers the OpenAPI fuzzer config (`app/schemathesis.toml`), the `--config-file`-is-global and GET-only-is-safe gotchas, and the first-run findings (a 500 on `/sessions/{id}/facts?tags=null` + ~9 undocumented-404 schema gaps). The two pages link to each other and to `obsidian-local-rest-api`. Mirrors a new auto-memory entry (`reference_router_env_tokens.md`).

## [2026-06-02T08:45:00] create | sqlite-query-param-guards + session-memory-storage | concepts/sqlite-query-param-guards.md, entities/session-memory-storage.md, entities/schemathesis.md, index.md

Wrote up the resolution of the two GET-route 500s schemathesis found (PR #51). New concept `sqlite-query-param-guards` distills the shared root cause — request values reaching a SQLite bind unvalidated — across the `json_extract '$[*]'` tag-filter `OperationalError` and the oversized-`offset` `OverflowError`, plus the `json_each`/clamp fixes and the paired 404-schema gap. New entity `session-memory-storage` documents the `SessionStorage` SQLite layer (tables, FTS5 triggers, lazy-singleton/per-op-connect conventions, storage-boundary guards). Updated the `schemathesis` entity's findings to current state with a Resolution (PR #51) section. The concept and entity cross-link to each other and to `schemathesis`; closes the single-strong-link gap the draft had.

## [2026-06-02T10:00:00] create | git-pr-workflow concept | concepts/git-pr-workflow.md, index.md

Distilled the git/PR workflow lessons from the three-PR session (#49/#50/#51) into a concept page. Covers: squash-merge meaning feature commits never become ancestors of `main` (so `git branch -d` refuses → use `-D`; `git log -- <file>` won't show the merged commit → verify with `git diff main <branch> -- <files>`); `gh pr merge --delete-branch` orphaning unpushed commits stacked on the local branch (recoverable via reflog); untracked/branch-local files "vanishing" on checkout being expected, not data loss; the stash-with-zero-overlap technique for touching another PR with a dirty tree; and the `gh config prefer_editor_prompt` non-tty blocker. Links to `schemathesis` and `router-auth-tokens` (the PRs where these surfaced).
