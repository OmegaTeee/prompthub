# Documentation Update Plan

## Problem

The current documentation is hard to navigate. New users need a clear starting point. Guides use inconsistent language and assume too much prior knowledge.

## Approach

Keep guides where they are (`app/docs/guides/`). Add a symlink and a quickstart at the project root. Refresh all guides to a consistent reading level.

## Changes

### 1. Root-level entry points

Add two things to the project root:

- **`QUICKSTART.md`** — Task-focused "do this now" guide (already drafted).
- **`guides` symlink** — Points to `app/docs/guides/` for quick browsing:
  ```bash
  ln -s app/docs/guides ~/prompthub/guides
  ```

No guides are moved. Cross-references, doc queue, and agent output paths stay intact.

### 2. Update `README.md`

Keep it short and stable. Add a links section:

- `QUICKSTART.md` — Get running in 5 minutes.
- `guides/` — User manuals for each feature.
- `app/docs/` — Developer docs, ADRs, architecture.

### 3. Refresh all user guides

Apply the readability standard (defined in `.claude/agents/user-manual.md`):

- Grade 9-10 reading level.
- Short sentences, common words, active voice.
- One action per step in numbered instructions.
- Plain-English analogies for complex concepts.
- "Why" before "how" in each section.
- Key-point summaries at the end of major sections.

Guides to refresh:

| # | Guide | Topic |
|---|-------|-------|
| 01 | quick-start-guide | First-time setup |
| 02 | prompt-enhancement-user-guide | How enhancement works |
| 03 | session-memory-guide | Memory system |
| 04 | openai-api-guide | OpenAI-compatible endpoint |
| 05 | troubleshooting-guide | Common problems and fixes |
| 06 | app-configuration-guide | Settings and config files |
| 07 | why-prompthub-comparison | Comparison with alternatives |
| 08 | advanced-power-user-manual | Power user workflows |
| 09 | open-webui-guide | Open WebUI integration |

### 4. Why this works

- Open the repo — short README tells you what this is and where to go.
- Want to use it — `QUICKSTART.md` gets you running with `./prompthub-start.zsh`.
- Need detail — `guides/` symlink puts user manuals one click away.
- Nothing moves — no broken links, no doc queue changes, no agent reconfiguration.
