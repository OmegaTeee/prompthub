# Wiki Maintenance & Migration Policy

This document defines the ongoing maintenance cadence for the PromptHub LLM Wiki, the automated link-health check, and the safe retirement workflow for source archive files after migration.

## 1. Maintenance Cadence

| Frequency | Activity | Owner | Tool / Artifact |
|-----------|----------|-------|-----------------|
| **Weekly** | Quick scan of `docs/wiki/index.md` for stale entries; run `check_wiki_links.py` and review JSON output. | Docs maintainer (rotating) | `docs/tools/check_wiki_links.py` |
| **Monthly** | Full wiki lint using `wiki-lint` command (orphan pages, stale index, broken body links, under-linked pages, log.md rotation). Move any `.to-delete/` files older than 30 days to permanent deletion after verification. | Docs maintainer | `~/.claude/commands/wiki-lint.md`, `docs/archive/.to-delete/` |
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

## 3. Migration Workflow (Archive → Wiki)

1. **Pick an archive file** in `docs/archive/`.
2. **Decide the target section** (`concepts` | `entities` | `sources` | `syntheses`).
3. **Choose a slug** (kebab-case, unique within the section) and a human title.
4. **Run the migration tool:**

   ```bash
   python docs/tools/migrate_to_wiki.py \
       docs/archive/YYYY-MM-DD-topic.md \
       <section> \
       <slug> \
       "Human Title"
   ```

   The tool:
   - Reads the archive markdown
   - Writes a new wiki page under `docs/wiki/<section>/<slug>.md` with front-matter:
     ```yaml
     ---
     slug: <slug>
     section: <section>
     status: archived-to-wiki
     original_file: ../../archive/<archive-name>.md
     ---
     # Human Title

     <original content>
     ```
   - Moves the original archive file to `docs/archive/.to-delete/<archive-name>.md` (staging).

5. **Update `docs/wiki/index.md`** — add a one-line entry in the appropriate section list:
   ```
   - [[<slug>]] — One-sentence summary.
   ```

6. **Run the link checker** to verify the new page’s outbound links resolve.

7. **Commit** the wiki page, index update, and the staged archive file together.

## 4. Source File Retirement Policy

| Stage | Location | Retention | Action |
|-------|----------|-----------|--------|
| **Staging** | `docs/archive/.to-delete/<file>.md` | 30 days minimum | Safe holding area; original content still recoverable. |
| **Verification** | — | During staging period | Run `wiki-lint`, confirm no broken links, confirm index entry exists. |
| **Purge** | `docs/archive/.to-delete/` | After 30 days + clean verification | Delete the staged file permanently (`rm`). |
| **Exception** | — | Indefinite | If a file is referenced by an open issue/PR/ADR, keep it in `.to-delete/` until the reference is resolved. |

**Automation hint:** a monthly cron can `find docs/archive/.to-delete -mtime +30 -delete` after the maintainer confirms the verification step.

## 5. Quick Reference Commands

```bash
# Migrate one file
python docs/tools/migrate_to_wiki.py docs/archive/2026-02-03-foo.md concepts foo-bar "Foo Bar"

# Check all wikilinks
python docs/tools/check_wiki_links.py

# Full wiki lint (read-only)
cat ~/.claude/commands/wiki-lint.md   # then run the steps manually, or
/hygiene                              # if the hygiene skill is installed
```

## 6. Governance

- **Owner:** Docs maintainer (rotating weekly) + Tech lead (quarterly).
- **Escalation:** If `check_wiki_links.py` reports >5 missing slugs, create a GitHub issue tagged `wiki-health`.
- **Policy changes:** Update this file and the `wiki-lint` command together; commit with `docs:` prefix.
