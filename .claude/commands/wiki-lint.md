---
description: Audit the PromptHub LLM-Wiki for orphan pages, broken wikilinks, and log rotation needs. Read-only; reports findings, doesn't fix.
allowed-tools: Bash, Read
---

Run the wiki lint checks defined by the `ph-docs` hygiene profile (`~/.claude/skills/hygiene/references/profiles/ph-docs.md`) against `docs/wiki/`. Report findings without making any changes.

Steps:

1. **Build master sets** by running:

   !`cd /Users/visualval/.local/share/prompthub && echo "=== on-disk pages ===" && find docs/wiki/{concepts,sources,entities,syntheses} -name "*.md" 2>/dev/null | sort && echo && echo "=== indexed pages (wikilinks in index.md) ===" && grep -oE '\[\[[^]]+\]\]' docs/wiki/index.md | sort -u && echo && echo "=== wikilinks in page bodies ===" && find docs/wiki/{concepts,sources,entities,syntheses} -name "*.md" -exec grep -HoE '\[\[[^]]+\]\]' {} \; 2>/dev/null && echo && echo "=== log.md size ===" && wc -l docs/wiki/log.md && grep -c '^## \[' docs/wiki/log.md`

2. **Run the six ph-docs checks** against the gathered data:

   - **Doc1 (HIGH)** — Orphan pages: on-disk page not in `index.md` wikilinks
   - **Doc2 (HIGH)** — Stale index: indexed wikilink with no matching `.md` file
   - **Doc3 (MEDIUM)** — Broken body wikilinks: `[[slug]]` in a page body where slug isn't on disk
   - **Doc4 (LOW)** — Under-linked pages: pages with fewer than 2 outbound `[[…]]` references
   - **Doc5 (LOW)** — log.md rotation: warn at 400+ entries, escalate at 500+ entries
   - **Doc6 (LOW, informational)** — `docs/notes/` coverage: count of legacy notes (by basename) that have a wiki counterpart vs not

3. **Report findings grouped by severity** in a markdown table:

   ```
   ## Wiki Lint Report

   ### HIGH
   | Check | Entry | Issue |
   |---|---|---|

   ### MEDIUM
   | ... |

   ### LOW (informational)
   | ... |

   ### Summary
   - X HIGH, Y MEDIUM, Z LOW
   - log.md: N entries (rotation at 500)
   - docs/notes coverage: M of K legacy files have wiki counterparts
   ```

4. **Do not remediate.** If the user wants fixes applied, they can ask explicitly or run `/hygiene` (the full hygiene skill, which knows how to apply edits with approval).
