# schemathesis

## Summary

[Schemathesis](https://schemathesis.readthedocs.io/) is a property-based API testing tool that reads an OpenAPI schema and generates fuzzing requests to check each endpoint against its declared contract (status codes, response shapes, content types). In PromptHub it's a fast smoke check of the router's `/openapi.json` surface, configured via `app/schemathesis.toml`. Installed locally via `uvx` and `pip`; pinned usage at v4.x.

## Details

### Config and invocation

Config lives at `app/schemathesis.toml` and sets the bearer header for `/v1/*` (see [[router-auth-tokens]]):

```toml
headers = { Authorization = "Bearer sk-prompthub-default-001" }
```

Run it (router must be listening on `:9090`):

```sh
cd app && schemathesis --config-file schemathesis.toml run \
    --include-method GET http://127.0.0.1:9090/openapi.json
```

### Two gotchas worth remembering

1. **`--config-file` is a GLOBAL option — it goes BEFORE `run`.** `schemathesis run --config-file ...` fails with *"No such option '--config-file'"*. The correct order is `schemathesis --config-file <path> run ...`.
2. **GET-only is the safe subset.** Without `--include-method GET`, schemathesis fuzzes every operation — including `POST /servers/{name}/start` (actually starts MCP servers), `/v1/chat/completions` (hits the local LLM repeatedly), and `/mcp/*` (mutates state). For a quick check, constrain to GET so the run has no side effects.

### Why the bearer

Schemathesis exercises the whole schema, which includes the `/v1/*` OpenAI-compat endpoints — the only routes that validate auth. Using the `default` test key (`sk-prompthub-default-001`) means those routes get real coverage instead of uniform 401s. Hardcoding it (rather than `${PH_API_TOKEN}`, which resolves to a *client* key) keeps the test config self-contained and reproducible.

### First-run findings (2026-06-02, GET-only)

516 cases → 13 unique failures:

- **1 server error (500):** `GET /sessions/{id}/facts?tags=null` returned `Internal Server Error` rather than handling the bad `tags` value. A deeper pass also surfaced a second 500 on `GET /sessions` from an oversized `offset`. Both were unguarded request values reaching SQLite — see [[sqlite-query-param-guards]].
- **~9 undocumented status codes:** routes like `GET /tools/{server}` correctly return 404 for an unknown resource, but the OpenAPI schema only declared 200/422. Schema-completeness gaps — fixed by adding the 404 to each route's `responses=`.
- A couple of schema-compliant-request rejections and one unsupported-method finding.

The split is instructive: schemathesis surfaces both real server faults (the 500s) and contract drift (routes whose actual responses aren't in the declared schema). Both are worth fixing, but only the 500s are behavioral defects.

### Resolution (PR #51)

Both 500s and the seven GET-route 404 gaps were fixed in PR #51. Re-running the
same GET-only pass dropped the Server-error count from 1 to 0 and undocumented
statuses from 10 to 2 (the remaining two are `400` input-rejections, a separate
class). The fix patterns are written up in [[sqlite-query-param-guards]]; the
storage layer they live in is [[session-memory-storage]].

## Related

- [[router-auth-tokens]] — explains the `/v1`-only auth boundary and why the `default` key is the right bearer for this config.
- [[obsidian-local-rest-api]] — another local HTTP service with an OpenAPI-style surface and bearer auth that the same schema-testing approach could target.

## Sources

- `app/schemathesis.toml` — the committed config (self-documenting header comments)
- `https://schemathesis.readthedocs.io/` — upstream docs
- Router OpenAPI schema at `http://127.0.0.1:9090/openapi.json` (FastAPI auto-generated)
