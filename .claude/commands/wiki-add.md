---
description: Add a page to the PromptHub LLM-Wiki at docs/wiki/. Delegates to the llm-wiki-ops-portable skill.
argument-hint: <type: concept|source|entity|synthesis> <slug-in-kebab-case> [optional body context]
---

Use the `llm-wiki-ops-portable` skill to add a new page to the PromptHub wiki at `docs/wiki/`.

Arguments provided: `$ARGUMENTS`

The first token of `$ARGUMENTS` is the page type — must be one of `concept`, `source`, `entity`, or `synthesis`. The second token is the page slug (lowercase, kebab-case, no `.md` extension). Any remaining tokens are optional body context to draft the page from.

Required steps:

1. **Parse arguments**: extract `<type>`, `<slug>`, and `<body context>` from `$ARGUMENTS`. If `<type>` or `<slug>` is missing or `<type>` is not in the allowed set, ask the user for them before proceeding.

2. **Confirm scope**: check `docs/wiki/<type>s/<slug>.md` doesn't already exist. If it does, ask whether to update the existing page or pick a different slug.

3. **Draft the page** using the skill's required format:
   - `# Page Title`
   - `## Summary` (2–3 sentences)
   - `## Details` (body content; expand from the user's body context if provided, otherwise ask what to write)
   - `## Related` (at least 2 `[[wikilink]]` cross-references to existing wiki pages — read `docs/wiki/index.md` to find candidates)
   - `## Sources` (external references)

4. **Update the spine**:
   - Add a one-line entry to `docs/wiki/index.md` under the correct section (Concepts / Sources / Entities / Syntheses), maintaining alphabetical order within the section.
   - Append a log entry to `docs/wiki/log.md`: `## [<ISO-timestamp>] create | <slug> | docs/wiki/<type>s/<slug>.md, index.md` followed by a one-paragraph summary.

5. **Report**: tell the user the new file path, the index entry added, and the wikilink targets used.

If the user's body context implies sources that should be wiki pages themselves but aren't yet, mention them as suggested follow-ups — do not silently create stub pages.
