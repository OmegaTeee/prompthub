# AGENTS.md

Use this file as the default onboarding context for AI coding agents working in this repository.
This file is intentionally cross-client so Claude Code, OpenCode, and future agentic tools can share the same repo contract.

## Why this repo exists

PromptHub is the local MCP router project for sharing MCP servers and centralizing client configurations across multiple AI clients.
The repo should preserve a single source of truth for routing behavior, config generation, enhancement logic, and cross-client conventions.
Prefer improving shared abstractions over adding one-off client-specific hacks.

## Agent roles

| Agent | Role | Typical use |
| --- | --- | --- |
| Claude Code | Primary high-trust implementer | Architecture, structural changes, nuanced refactors, documentation, broad repo work |
| OpenCode | Backup local coding agent | Local-first implementation, terminal workflows, second-pass execution, fallback when Claude is unavailable |
| Copilot / IDE assist | Inline helper | Autocomplete, snippets, small local edits, quick chat inside the editor |

All agents should follow the same repo conventions unless a task explicitly requires a client-specific behavior.

## Repo priorities

- Keep PromptHub centralized.
- Preserve compatibility across supported clients unless the task explicitly allows a breaking change.
- Prefer generator/source fixes over manual edits to derived output.
- Keep Claude-primary and OpenCode/LM Studio-backup workflows aligned where practical.
- Update durable docs when conventions, paths, or generated outputs change.

## Supported clients

Current supported-now clients include:

- `vscode-mcp`
- `perplexity-desktop-mcp`
- `claude-code-mcp`
- `claude-desktop-mcp`
- `lm-studio-mcp`
- `raycast-mcp`

When editing shared config logic, think in terms of cross-client consistency first and per-client customization second.

## Important paths

- Repo root: `~/prompthub`
- Docs root: `~/prompthub/docs`
- Agent docs: `~/prompthub/docs/agent-guides`
- Shared enhancement rules: `~/prompthub/app/configs/enhancement-rules.json`
- Repo knowledge files: `~/prompthub/.firecrawl/`
- Local runtime  `~/.local/share/prompthub/`

Read these before large or cross-cutting changes:

- `docs/agent-guides/project-map.md`
- `docs/agent-guides/build-test-verify.md`
- `docs/agent-guides/config-locations.md`
- `docs/architecture/README.md`
- `docs/guides/06-client-configuration-guide.md`

## Operating rules

- Treat PromptHub as the source of truth for MCP server sharing and centralized client configuration.
- Prefer editing source files, templates, or generators instead of patching generated output directly.
- Do not invent new config shapes or naming conventions when an existing pattern already exists.
- Keep MCP server labels, transport language, and env var names consistent across clients where possible.
- Do not delete historical, failed, or experimental config paths unless cleanup is explicitly in scope.
- For local-model workflows, assume LM Studio is the default local LLM backend unless the task states otherwise.
- If code, docs, and scraped knowledge disagree, trust the current repository and active docs over `.firecrawl/` references.

## Validation rules

- Use the smallest effective validation step first.
- If changing config generation, inspect the generated output for the affected client.
- If changing routing or transport behavior, validate both happy path and at least one fallback or failure path.
- Do not claim success unless you ran the relevant command or inspected the relevant artifact.
- Summaries should explicitly name affected clients, docs, generators, and risks.

For exact validation expectations, read `docs/agent-guides/build-test-verify.md`.

## Documentation rules

- Keep durable project guidance in stable docs, not temporary tracking files.
- Update user-facing docs when user-visible behavior changes.
- Update agent-facing docs when repo conventions, paths, or workflows change.
- Keep documentation concise, current, and easy for future agents to scan.

Recommended doc locations:

- User guides: `docs/guides/`
- Architecture docs: `docs/architecture/`
- Agent docs: `docs/agent-guides/`
- Historical material: `docs/archive/`
- Working notes and research: `docs/notes/`

## Change style

- Make small, reviewable changes.
- Avoid mixing unrelated fixes in one pass.
- For large refactors, explain intended impact before touching many files.
- Preserve stable abstractions unless they clearly increase duplication or fragility.
- When uncertain, choose the option that keeps PromptHub more centralized, not less.

## Progressive disclosure

Read only the guides needed for the current task:

- Repo structure: `docs/agent-guides/project-map.md`
- Validation and verification: `docs/agent-guides/build-test-verify.md`
- Config and runtime paths: `docs/agent-guides/config-locations.md`
- Additional guides may be added under `docs/agent-guides/` for routing and client-specific patterns.

## Output expectations

In the final summary:

- Explain what changed in plain language.
- List affected files, clients, generators, and docs.
- Mention what validation was run or what artifacts were inspected.
- Call out any migration work, follow-up tasks, or compatibility risks.
