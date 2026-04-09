# Config locations

This guide helps coding agents distinguish between source files, generated artifacts, repository documentation, and local runtime data used by PromptHub.

## Core locations

- Repo root: `~/prompthub`
- Docs root: `~/prompthub/docs`
- Agent docs: `~/prompthub/docs/agent-guides`
- Shared enhancement rules: `~/prompthub/app/configs/enhancement-rules.json`
- Repo-managed client configs: `~/prompthub/clients/`
- Local runtime  `~/.local/share/prompthub/`
- Repo knowledge files: `~/prompthub/.firecrawl/`

## How to think about locations

- `app/` contains implementation and likely source-of-truth logic.
- `app/configs/` is shared router configuration space; these files are usually
  edited directly when the router's runtime behavior changes.
- `clients/` contains repo-managed client config files and setup scripts;
  prefer updating those files rather than editing app-installed copies.
- `docs/` contains durable documentation; prefer updating active docs instead of archived notes when conventions change.
- `~/.local/share/prompthub/` is outside the repo and should be modified carefully, only when the task clearly requires local runtime changes.

## Source versus generated files

Before editing a config-related file, determine which category it belongs to:

- Source file — intended to be edited directly.
- Template or generator input — edits flow into one or more generated outputs.
- Generated artifact — should usually be regenerated, not hand-maintained.
- Local runtime state — environment-specific data outside the repo.

If uncertain, search nearby docs and code paths before editing.

## Documentation locations

- User guides: `docs/guides/`
- Architecture decisions: `docs/architecture/`
- API docs: `docs/api/`
- Module docs: `docs/modules/`
- Agent-oriented docs: `docs/agent-guides/`
- Historical context: `docs/archive/`
- Working notes and research: `docs/notes/`

## Editing rules

- Prefer editing the source file in `clients/` or `app/configs/` over patching
  installed app configs or machine-local copies.
- Do not move or rename important config paths unless the task explicitly includes migration work.
- When a config path changes, update docs and any examples that reference it.
- Keep path references consistent between AGENTS.md and docs/agent-guides.

## Local runtime caution

Use extra care with `~/.local/share/prompthub/`:

- It is not the same as the git-tracked repository.
- It may contain machine-specific or user-specific state.
- Changes there should be deliberate and easy to explain.
- Repo improvements should usually happen in `~/prompthub`, not only in local runtime storage.

## Repo knowledge files

Use `.firecrawl/` as supporting context, not as the primary source of project truth.
If repo behavior, code, and scraped knowledge disagree, prefer the actual repository and current docs.
