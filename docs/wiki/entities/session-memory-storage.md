# session-memory-storage

## Summary

`SessionStorage` (`app/router/memory/storage.py`) is the SQLite-backed
persistence layer for PromptHub's session memory system. It owns three tables —
sessions, facts, and memory blocks — plus FTS5 full-text indexes, and exposes
async CRUD used by the `/sessions/*` routes. It is the storage boundary where
request-derived values (tags, pagination, search queries) meet SQL, which makes
it the layer responsible for [[sqlite-query-param-guards]].

## Details

### Schema

Database at `~/.prompthub/memory.db` (override via `MEMORY_DB_PATH`). Three base
tables:

- `sessions` (id, client_id, timestamps, status, context_summary, memory_mcp_sync)
- `session_facts` (id, session_id, fact, `tags TEXT DEFAULT '[]'`, relevance_score, source)
- `session_memory_blocks` (session_id, key, value, expires_at; `UNIQUE(session_id, key)`)

Two FTS5 contentless virtual tables (`session_facts_fts`, `session_blocks_fts`)
mirror the base tables via AFTER INSERT/UPDATE/DELETE triggers, backfilled on
init when stale. They power BM25-ranked cross-session `search()`.

### Conventions

- **Lazy singleton** via `get_session_storage()`; schema created once under an
  `asyncio.Lock` guard.
- **Per-op `aiosqlite.connect()`** — no long-lived connection.
- **`db_path: Path | None = None`** with lazy `get_settings()` resolution inside
  the `if` branch, so tests pass an explicit `tmp_path` and circular imports are
  avoided.
- **client_id enrichment** from the audit context (`X-Client-ID`) when callers
  omit it; `search()` scopes to the caller's client unless `cross_client=True`.

### Storage-boundary hardening

Two patterns guard the SQL surface against arbitrary request input (see
[[sqlite-query-param-guards]] for the full reasoning):

- **Tag filtering** uses `json_each(tags)` + `EXISTS (... WHERE value IN (...))`
  to test array membership. (`json_extract`'s path grammar has no `$[*]`
  wildcard, so it cannot express "array contains".)
- **Pagination** (`limit`/`offset` in `list_sessions`, `limit` in `get_facts`)
  is clamped to SQLite's signed-64-bit bind range via `_clamp_pagination`;
  `search()` clamps its `limit` to `[1, 100]` the same way. Unclamped values
  raise `OverflowError` at bind time.
- **`search()`** catches `aiosqlite.OperationalError` (malformed FTS5 MATCH) and
  returns `[]` rather than 500-ing.

## Related

- [[sqlite-query-param-guards]] — the cross-cutting pattern this layer
  implements: validate/clamp request values before they reach a SQLite bind.
- [[schemathesis]] — the OpenAPI fuzzer that surfaced two unguarded-input 500s
  in this layer (`get_facts` tag filter, `list_sessions` pagination).

## Sources

- `app/router/memory/storage.py` — the implementation
- `app/router/memory/router.py` — the `/sessions/*` route handlers that call it
- `app/tests/test_memory.py` — unit coverage (CRUD, tag filter, pagination, FTS search)
