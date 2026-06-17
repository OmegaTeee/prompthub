# Guarding Query Params Before They Reach SQLite

## Summary

Two unrelated `500`s on the router's GET session routes shared one root cause: a
request value flowed unvalidated into a SQLite query, where the *driver* — not
the application — decided to raise. The durable fix is to never form the invalid
bind (correct SQL, clamped integers), not to catch the exception after the fact.

## Details

Both bugs were found by the GET-only [[../entities/schemathesis]] fuzz against
`/openapi.json` and both returned an unhandled `500` where the schema promised
`200`/`422`. Both live in [[../entities/session-memory-storage]].

### 1. Invalid `json_extract` path wildcard

`get_facts` filtered tags with `json_extract(tags, '$[*]') LIKE ?`. SQLite's
`json_extract` path grammar has **no `$[*]` array wildcard** (that belongs to
`json_each`/`json_tree`), so it raised `OperationalError: bad JSON path: '$[*]'`
for *any* non-empty `tags` value. The fuzzer tripped it with `tags=null`, which
the route parses to the truthy list `["null"]`. The query was effectively dead
code — it could only throw, never match.

Fix: `json_each` (a table-valued function that expands the JSON array into rows)
+ `EXISTS (... WHERE value IN (...))` — the correct "array contains any of
these" query. Unknown tags now return `200 []`.

### 2. Integer overflow on pagination

`list_sessions` bound `offset`/`limit` straight into `LIMIT ? OFFSET ?`. A
fuzzed `offset=270164148743501611008` exceeds SQLite's signed-64-bit bind range
(`2**63-1`), raising `OverflowError: Python int too large to convert to SQLite
INTEGER`. Fix: a `_clamp_pagination` helper clamps to `[0, 2**63-1]`, mirroring
the clamp already present in `SessionStorage.search()`.

### The general principle

A query parameter typed `int` in FastAPI is an *unbounded* Python int; a JSON
string like `"null"` is still a truthy string. Neither is safe to hand to SQLite
verbatim. Validate or clamp at the storage boundary, and prefer the SQL
construct that *can't* be malformed over a `try/except` that papers over one
that can. The existing `search()` clamp is the local idiom to copy.

### Paired finding: schema honesty

Seven GET-by-resource routes returned `404` for unknown resources but declared
only `200`/`422`, so the OpenAPI schema misrepresented reality — and the fuzzer
flagged every legitimate 404 as "undocumented status code". Adding
`responses={404: …}` to those decorators makes the schema match behavior so
fuzzers and clients stop tripping on correct responses.

After both fixes, the GET-only schemathesis Server-error count dropped from 1 to
0, and the undocumented-status findings from 10 to 2 (the remaining two are
`400` input-rejections, a separate class).

## Related

- [[../entities/session-memory-storage]] — the SQLite layer where both bugs lived and where
  the guards now sit.
- [[../entities/schemathesis]] — the property-based OpenAPI fuzzer that surfaced both 500s
  and the 404 schema gaps.

## Sources

- PR #51 (`test/schemathesis-router-check`) — the fix commit
- `app/router/memory/storage.py` — `get_facts`, `list_sessions`, `_clamp_pagination`
- `app/schemathesis.toml` — the fuzz config that found the faults
