# llm-wiki-ops-portable

## Summary

A Claude Code skill implementing the Karpathy LLM Wiki pattern for any workspace. Installed user-level at `~/.claude/skills/llm-wiki-ops-portable/SKILL.md` and auto-discovered. Powers PromptHub's wiki at `docs/wiki/` (see [[llm-wiki-setup]] for project-specific framing).

## Details

The skill is one file: `SKILL.md`, ~2.4KB. It defines a 4-section wiki layout (`concepts/`, `sources/`, `entities/`, `syntheses/`), a page format (Title / Summary / Details / Related / Sources), and operational rules (`grep -rli` for search, double-bracket wikilinks for cross-refs, one topic per page, ≤100 lines). The skill ships no Python tooling, no seed articles (despite referencing a `.seed-manifest.json` that isn't bundled), and no lint commands — enforcement happens via operator discipline and the project's [[ph-docs-hygiene-profile]].

Compared to its sibling `llm-wiki-skill` (also distributed as a zip in `docs/notes/research/`): the heavy variant has a 3-layer `raw/`/`generated/`/`SCHEMA.md` architecture, mandatory YAML frontmatter, Python ingest+lint scripts, and *requires* the agent to be invoked at the wiki root (`cd docs/wiki/` before any op, else the skill aborts). The portable variant trades that rigor for drop-in friendliness — it works from anywhere in the workspace and tolerates no-frontmatter pages.

Trigger phrases: invocation via `/skill llm-wiki-ops-portable` or natural-language hints like "add this to the wiki" / "make a wiki page for X" / "search the wiki for Y". The project also exposes thin slash-command wrappers (`/wiki-add`, `/wiki-find`, `/wiki-lint`, `/wiki-log`) that delegate to the skill — see [[llm-wiki-setup]].

## Related

- [[llm-wiki-setup]] — how this skill is used in PromptHub specifically
- [[ph-docs-hygiene-profile]] — the audit layer that catches drift the skill doesn't enforce

## Sources

- `~/.claude/skills/llm-wiki-ops-portable/SKILL.md` — the skill itself
- Karpathy LLM Wiki pattern — original inspiration
- `docs/notes/research/llm-wiki-skill.zip` — the heavier sibling, for comparison
