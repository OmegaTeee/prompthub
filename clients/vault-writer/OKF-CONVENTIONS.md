# OKF Conventions for Vault Documents

All documents you create or edit are **OKF** (Open Knowledge Format): a Markdown
file with YAML frontmatter. Follow these rules exactly.

## Required frontmatter (every file)

```yaml
---
type: <pr-brief | note | concept | reference>
resource: <kebab-case-stable-id>      # unique, stable, matches filename stem
tags: [<topic>, <topic>]              # 1-6 lowercase kebab tags
timestamp: <YYYY-MM-DD>               # date authored/last revised
---
```

Extra keys are allowed (e.g. `status`, `pr`, `author`) but the four above are mandatory.

## Body conventions

- First line after frontmatter is an `# H1` matching the document's human title.
- Use `[[wikilinks]]` to reference other notes (graph-shaped knowledge).
- Prefer short sections with `##` headers. No HTML.

## PR-brief body structure (`type: pr-brief`)

```markdown
# <Title>

## Summary
<2-3 sentences: what changes and why>

## Motivation
<the problem / context>

## Changes
- <bullet per notable change>

## Risks & Mitigations
- <risk> → <mitigation>

## Links
- [[related-note]]
```

## Hard rules

- Never write a file without complete required frontmatter.
- `resource` must equal the filename without `.md`.
- Keep prose tight; this is a brief, not an essay.
