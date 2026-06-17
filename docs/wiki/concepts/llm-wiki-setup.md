# LLM-Wiki Setup in PromptHub

## Summary

PromptHub maintains a wiki at `docs/wiki/` as a successor to `docs/notes/` — agent-curated, cross-linked Markdown that compounds in value as topics are revisited. Driven by the [[../entities/llm-wiki-ops-portable]] skill, seeded 2026-06-01 with the legacy notes intentionally left to age out organically rather than migrated en masse.

## Details

The wiki replaces the freeform note-taking pattern in `docs/notes/` (5 subdirs, 36 md files at scaffold time) with a structured 4-section layout: `concepts/` (distilled ideas), `sources/` (external material summaries), `entities/` (named tools/services/people), `syntheses/` (cross-cutting analysis). Every page is one topic, ≤100 lines, with mandatory wikilink style cross-references to at least 2 other pages.

Two files form the *spine*: `index.md` is the page registry (one-line entry per page, sectioned by type), and `log.md` is the append-only change log (`## [ISO-timestamp] action | subject | files`). Skipping either degrades the wiki into an orphan-page swamp, which is why [[../entities/ph-docs-hygiene-profile]] explicitly audits these.

The skill is intentionally **portable** — it doesn't require Python scripts, doesn't require the agent to be invoked at the wiki root (unlike its heavier sibling `llm-wiki-skill`), and uses plain `grep` for search. The trade-off is looser enforcement: the heavy variant lints orphans and broken links via dedicated Python tools; the portable variant relies on the operator and on hygiene-profile checks to catch the same drift.

Coexistence with `docs/notes/` is deliberate: the user picked "age out naturally" as the migration strategy. As topics resurface, the wiki version gets written instead of patching the old note. The legacy directory will shrink over months, not days.

## Related

- [[../entities/llm-wiki-ops-portable]] — the skill that powers this wiki
- [[../entities/ph-docs-hygiene-profile]] — the hygiene profile that audits the wiki's structural integrity

## Sources

- `~/.claude/skills/llm-wiki-ops-portable/SKILL.md` — skill spec
- `docs/notes/research/llm-wiki-skill.zip` — heavy variant reference (not installed)
- Karpathy's LLM Wiki pattern (concepts/sources/entities/syntheses)
