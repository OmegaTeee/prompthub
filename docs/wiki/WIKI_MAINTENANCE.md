# Wiki Maintenance & Migration Policy

This document defines the ongoing maintenance cadence for the PromptHub LLM Wiki and the automated link-health check.

## 1. Maintenance Cadence

| Frequency | Activity | Owner | Tool / Artifact |
|-----------|----------|-------|-----------------|
| **Weekly** | Quick scan of `docs/wiki/index.md` for stale entries; run `check_wiki_links.py` and review JSON output. | Docs maintainer (rotating) | `docs/tools/check_wiki_links.py` |
| **Monthly** | Full wiki lint using `wiki-lint` command (orphan pages, stale index, broken body links, under-linked pages, log.md rotation). | Docs maintainer | `~/.claude/commands/wiki-lint.md` |
| **Quarterly** | Audit wiki structure against the four-section model (concepts, entities, sources, syntheses). Consolidate near-duplicate pages, update cross-links, refresh the maintenance policy if conventions drift. | Tech lead / Docs owner | Manual review + `wiki-lint` summary |

## 2. Automated Link Health Check

**Script:** `docs/tools/check_wiki_links.py`

**What it does:**
- Walks `docs/wiki/{concepts,entities,sources,syntheses}/*.md`
- Extracts every `[[slug]]` wikilink
- Verifies the target file `docs/wiki/<section>/<slug>.md` exists in any section
- Emits a JSON report:

```json
{
  "files": {
    "sources/foo.md": ["missing-slug-1", "missing-slug-2"]
  },
  "summary": {
    "missing_global_slugs": ["missing-slug-1", "missing-slug-2"]
  }
}
```

**Integration:**
- Add a CI step (GitHub Actions / pre-commit) that runs the script and fails on non-empty `missing_global_slugs`.
- Weekly cron (or scheduled workflow) posts the JSON to a monitoring channel.

## 3. Quick Reference Commands

```bash
# Check all wikilinks
python docs/tools/check_wiki_links.py

# Full wiki lint (read-only)
cat ~/.claude/commands/wiki-lint.md   # then run the steps manually, or
/hygiene                              # if the hygiene skill is installed
```

## 4. Governance

- **Owner:** Docs maintainer (rotating weekly) + Tech lead (quarterly).
- **Escalation:** If `check_wiki_links.py` reports >5 missing slugs, create a GitHub issue tagged `wiki-health`.
- **Policy changes:** Update this file and the `wiki-lint` command together; commit with `docs:` prefix.
