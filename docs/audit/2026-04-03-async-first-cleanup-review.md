# Async-first cleanup review — 2026-04-03

This note captures code-review findings after removing the legacy `app/router/clients/` wrapper and auditing remaining cleanup candidates.

## Completed

- Refactored `app/router/routes/client_configs.py` to use CLI-owned generation logic directly.
- Removed the legacy `app/router/clients/` package from the active router tree.
- Moved the old wrapper backup to `./.trash/app-router-clients-deleted-legacy` for pre-commit recovery.

## Confirmed current state

- Runtime startup already uses `await registry.load_async()` in `app/router/main.py`.
- `app/cli/` is now the active implementation path for client config generation.
- Top-level `clients/` remains the canonical repo-owned location for generated client config artifacts.

## Next recommended patch

### 1) Finish async-first cleanup in `app/router/servers/registry.py`

Search findings show the registry still contains deprecated sync compatibility methods and internal sync persistence paths.

Observed:
- `app/router/main.py` uses `await registry.load_async()` at startup.
- `app/router/servers/registry.py` still contains deprecated sync `load()` / `save()` methods.
- `app/router/servers/registry.py` also appears to persist state through sync save paths during mutation flows like add/remove.

Recommended patch for Claude:
- Add async mutation methods: `add_async()`, `remove_async()` (mirrors the existing `load_async()` / `save_async()` naming).
- Convert internal persistence in mutation flows to `await save_async()`.
- Migrate any async route or supervisor callers to the async mutation methods.
- Remove deprecated sync `load()` / `save()` only after grep confirms no callers remain.
- Remove the inline `# Claude review notes` block at the bottom of `registry.py` (lines 302–306) — this audit doc is the canonical record.

Suggested grep:
- `rg "\.load\(|\.save\(|load_async\(|save_async\(" app/router app/tests`
- `rg "\.add\(|\.remove\(|add_async\(|remove_async\(" app/router app/tests`

### 2) Audit route and supervisor mutation call sites

Before removing sync methods, inspect any code paths that mutate the registry and confirm they already run in async contexts and can await persistence safely.

High-value files to inspect next:
- `app/router/routes/servers.py`
- `app/router/servers/supervisor.py`
- Any admin/install/delete endpoints that write `mcp-servers.json`

### 3) Leave validator migration guards in place for now

`app/cli/validator.py` still checks for legacy config mistakes such as `AGENTHUB_URL`.

Recommendation:
- Keep these checks until older client configs are no longer expected in the field.
- They provide useful migration safety and are not causing structural confusion.

## Documentation recommendation

Yes — keeping review notes in `docs/audit/` is a good fit for this kind of patch planning because:
- the repo already has an existing `docs/audit/` area,
- these notes are implementation-audit oriented,
- and Claude/OpenCode can consume a focused patch brief faster than reconstructing context from code comments.

Recommended filename:
- `docs/audit/2026-04-03-async-first-cleanup-review.md`

## Suggested next testing target — OpenCode

[OpenCode](https://github.com/opencode-ai/opencode) is a terminal-based AI coding agent (similar to Claude Code). It supports MCP stdio servers natively.

Verify whether it should be introduced as:
- a new `ClientType` in `app/cli/models.py` with a concrete config path/install strategy (likely — it uses `~/.config/opencode/config.json` for MCP), or
- an HTTP-style integration similar to Open WebUI if it does not use stdio bridge config.
