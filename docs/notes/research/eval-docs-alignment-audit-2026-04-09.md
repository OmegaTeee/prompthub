---
title: "Docs Alignment Audit Summary"
status: final
created: 2026-04-09
updated: 2026-04-09
tags: [research, docs, audit, architecture, glossary]
---

# Docs Alignment Audit Summary

## Scope

This note summarizes the April 9, 2026 documentation cleanup pass across
PromptHub's active docs, agent docs, client docs, and historical material.

## What changed

- Rewrote the active architecture overview to match the current
  router/bridge/proxy split and LM Studio-backed runtime.
- Updated active guides and client READMEs to remove deleted Python CLI and
  `/configs/*` workflows in favor of repo-managed `clients/` files and
  `setup.sh` scripts.
- Added glossary-driven terminology cleanup across active docs so `router`,
  `bridge`, `proxy`, `enhancement`, `privacy level`, and `circuit breaker` are
  used more consistently.
- Moved the dashboard idea documents from `docs/notes/dashboard/` to
  `docs/notes/plans/`.
- Added explicit historical framing to ADRs, research notes, and superpowers
  specs/plans that preserve older Ollama-era examples.
- Fixed the archive index and added retention guidance in
  `docs/archive/README.md`.

## Audit outcome

Active documentation is now substantially cleaner. Remaining mentions of
`Ollama` in active surfaces are intentional:

- compatibility guidance in `docs/guides/10-local-llm-recommendations.md`
- vendor/reference wording in `clients/_cherry-studio/cherry-studio-llm.txt`

Historical docs still contain older terms by design, but they are now marked so
they do not read as current implementation guidance.

## Recommendations

- Keep YAML frontmatter mandatory for `docs/notes/` content and normalize older
  research notes that still lack it.
- Do not add frontmatter broadly to guides, ADRs, or README index files unless
  the project later adopts a documentation site or metadata-driven build step.
- Keep ADRs and migration/audit notes that explain current constraints.
- Consider deleting or condensing low-value archive items that are mostly
  completed task logs.

## Related docs

- `docs/architecture/README.md`
- `docs/glossary.md`
- `docs/archive/README.md`
- `docs/notes/README.md`
