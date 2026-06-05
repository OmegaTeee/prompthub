---
description: Show the last N entries from the PromptHub LLM-Wiki change log (default 10).
argument-hint: [N — number of entries to show, default 10]
allowed-tools: Bash, Read
---

Read the last N entries from `docs/wiki/log.md` and present them in a compact, scannable format.

Arguments provided: `$ARGUMENTS`

Steps:

1. **Parse N**: if `$ARGUMENTS` is a positive integer, use it. Otherwise default to 10. If `$ARGUMENTS` is `all`, show every entry.

2. **Find the last N `## [...]` entry headers** and extract each entry's:
   - Timestamp
   - Action (create / ingest / update / lint / archive / delete)
   - Subject
   - Files
   - First sentence of the body

   Use the bash:

   !`cd /Users/visualval/.local/share/prompthub && awk '/^## \[/{n++; if(n>20) exit} 1' docs/wiki/log.md | tail -150`

   (then trim to the actual N the user asked for during your processing)

3. **Present as a compact table**:

   ```
   | Time | Action | Subject | Files |
   |---|---|---|---|
   | YYYY-MM-DD HH:MM | create | <subject> | <comma-separated> |
   ```

4. **Footer summary**:
   - Total entries in `log.md`
   - Headroom to rotation threshold (500 - current)
   - Most recent action timestamp

5. **Don't modify the log** — read-only command. If the user asks to add an entry, suggest `/wiki-add` (which writes its own log entry) or doing it directly via Edit.
