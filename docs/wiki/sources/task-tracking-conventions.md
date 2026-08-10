---
slug: task-tracking-conventions
section: sources
status: archived-to-wiki
related: docs/guides/project-todos.md
---
# Task‑Tracking Conventions

**Origin**: `TODOS.reordered.md` – a consolidated Project TODO list (Feb 2026).

## Purpose
Provide a reusable, searchable reference for how the Prompthub team tracks
ongoing work, prioritises tasks, and records decision context.

## Core Elements
1. **Date‑prefixed entries** – Each task starts with `YYYY‑MM‑DD‑` for easy
   chronological sorting.
2. **Status markers** – `✅` (complete), `⚠️` (in‑progress), `❌` (blocked),
   `🟢` (ready).
3. **Owner tags** – `#owner:<initials>` for quick responsibility lookup.
4. **Explicit scope** – Brackets `[]` denote the affected module or feature.
5. **Link to Documentation** – When a task resolves a decision, add a wiki
   link pointing to the relevant `concepts` or `syntheses` page.

## Example Entry
```markdown
2026-04-15 ✅ [router] #owner:js – Refactor `router/servers/supervisor.py`
  – Consolidate env‑resolution logic into `resolve_server_env` (see
  [[keyring‑integration‑complete]]).
```

## When to Use
- **New feature work** – Create a TODO entry before implementation to
  capture scope and owner.
- **Bug triage** – Record the bug, status, and link to the associated
  troubleshooting guide.
- **Documentation updates** – Add an entry when a wiki page or guide needs
  revision.

## Maintenance Tips
- **Weekly Review** – Scan the `docs/TODOS.reordered.md` file and move
  completed items to the archive section of this page.
- **Searchability** – Use the `#owner` tag to filter tasks by assignee.
- **Cross‑link** – After completing a task, add a `[[keyring-integration-complete]]` entry so
  future readers can trace the change.

## Related Pages
- `docs/guides/project-todos.md` – Full TODO master list with links to this
  source page.
- `docs/architecture/ADR-010-task‑management.md` – Decision record for the
  TODO process.
