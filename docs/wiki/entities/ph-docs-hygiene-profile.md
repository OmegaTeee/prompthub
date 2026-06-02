# ph-docs Hygiene Profile

## Summary

A hygiene-skill profile at `~/.claude/skills/hygiene/references/profiles/ph-docs.md` that audits PromptHub's wiki structure — orphan pages, broken wikilinks, log rotation, and `docs/notes/` coverage. Sibling to `ph-mcps`, `ph-router`, and `ph-clients`; activates whenever `docs/wiki/index.md` and `docs/wiki/log.md` both exist.

## Details

The profile runs six checks (`Doc1`–`Doc6`) covering distinct drift classes that the [[llm-wiki-ops-portable]] skill can't catch on its own. Doc1 flags pages on disk but missing from `index.md` (HIGH — breaks discoverability). Doc2 catches the inverse: index entries pointing at non-existent files (HIGH — broken navigation). Doc3 walks every page body for double-bracket slug references and flags ones that don't resolve (MEDIUM). Doc4 enforces the soft "≥2 outbound links per page" rule (LOW). Doc5 watches `log.md` line count and warns near the 500-entry rotation threshold (LOW). Doc6 reports a coverage *number* of `docs/notes/` files that have a wiki counterpart by slug — informational, not actionable per-file.

The profile fills the gap between the heavy `llm-wiki-skill`'s Python lint tools (which would enforce orphans/broken-links automatically) and the portable variant's looser conventions (which rely on operator discipline). It runs whenever the user invokes `/hygiene` from PromptHub cwd, alongside the three sibling profiles. See [[llm-wiki-setup]] for the wiki context that motivated it.

The Doc6 check is deliberately *informational*: the project chose "age out naturally" as the migration strategy for `docs/notes/` → wiki. Flagging individual unmigrated notes would push toward bulk migration the user explicitly didn't want. Reporting the *number* instead lets the trend be observed over time without prescribing per-file action.

## Related

- [[llm-wiki-setup]] — the wiki this profile audits
- [[llm-wiki-ops-portable]] — the skill whose conventions the checks enforce

## Sources

- `~/.claude/skills/hygiene/references/profiles/ph-docs.md` — profile spec
- `~/.claude/skills/hygiene/SKILL.md` — parent hygiene skill
- Sibling profiles in the same directory: `ph-mcps`, `ph-router`, `ph-clients`
