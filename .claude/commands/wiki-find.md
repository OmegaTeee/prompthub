---
description: Search the PromptHub LLM-Wiki for a term across all pages.
argument-hint: <search term — quoted if multi-word>
allowed-tools: Bash, Read
---

Search the PromptHub LLM-Wiki at `docs/wiki/` for the given term and report matches.

Arguments provided: `$ARGUMENTS`

Steps:

1. **Run case-insensitive recursive grep** across all wiki pages (excluding the spine files unless the query explicitly targets them):

   !`grep -rilnE "$ARGUMENTS" /Users/visualval/.local/share/prompthub/docs/wiki/ --include="*.md" | grep -v '/log.md$' | head -30`

2. **For each matching file**, read it (briefly) and extract:
   - The page title (first `#` heading)
   - The Summary section (the 2–3 sentence intro under `## Summary`)
   - The line number(s) where the term appears in `## Details`

3. **Group results by section** (concepts / sources / entities / syntheses), since the wiki layout maps directory → page type.

4. **Suggest follow-ups**:
   - If 0 matches: suggest creating a wiki page on the topic (`/wiki-add` shortcut) and check whether the legacy `docs/notes/` has anything by running `grep -rilE "$ARGUMENTS" /Users/visualval/.local/share/prompthub/docs/notes/ --include="*.md" | head -10`. Surface those notes as candidates to synthesize.
   - If many matches (>10): suggest narrowing or creating a synthesis page that combines them.
   - If 1–2 matches: just present them.

5. **Don't modify any wiki files** — this is a read-only search command.
