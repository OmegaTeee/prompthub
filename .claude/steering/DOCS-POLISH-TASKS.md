# Documentation polish tasks (low-level)

Task list derived from PR review of commit 4a88b56 (docs overhaul). All items addressed in patch.

## Completed (2026-02-14)

- [x] **README.md** — Add Phase 5 to project status table; clarify L2 cache as "planned"
- [x] **app/docs/api/openapi.yaml** — Describe cache as "L1 in-memory; L2 semantic planned"; set `contact.url` to repo (OmegaTeee/prompthub)
- [x] **.claude/steering/tech.md** — Add note about `audit_admin_action` / `audit_credential_access` wrappers in Audit Events section
- [x] **app/docs/modules/README.md** — Change "1 of 11" → "1 of 12" and 9.1% → 8.3% to match COVERAGE-ANALYSIS.md
- [x] **CHANGELOG.md** — Move Unreleased content into [0.1.4]; leave Unreleased as "(No changes yet.)"
- [x] **.github/awesome-copilot-index.md** — Update "Last Updated" to February 14, 2026

## Optional follow-ups (not patched)

- OpenAPI: add `operationId` or response examples for any new endpoints that lack them (if you want stricter tooling).
- README: add link to OpenAPI spec (e.g. `/docs` or static file) if you serve it.
