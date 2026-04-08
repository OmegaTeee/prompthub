# Project map

This guide helps coding agents understand the structure of the PromptHub repository before making broad or cross-cutting changes.

## Repository purpose

PromptHub is the local MCP router project for sharing MCP servers and centralizing client configurations across multiple AI clients.
The repo should preserve a single source of truth for routing behavior, client configuration generation, and shared enhancement logic.

## High-level structure

- `app/` — main application code and internal implementation details.
- `app/configs/` — managed client-facing configuration assets and related config logic.
- `app/configs/enhancement-rules.json` — important shared enhancement/config rules file.
- `docs/` — human and agent-facing documentation.
- `docs/api/` — API reference and integration details.
- `docs/architecture/` — ADRs and architecture notes; read before major refactors.
- `docs/guides/` — user-facing guides and configuration documentation.
- `docs/modules/` — module-level docs such as server-related explanations.
- `docs/notes/` — research, plans, dashboards, and working notes.
- `docs/archive/` — archived historical docs; use for context, not current source of truth.
- `.firecrawl/` — repo knowledge files and scraped references used to improve coding assistance.
- `scripts/` — repo wrapper commands and operational helpers for development, testing, router management, and maintenance.
- `~/.local/share/prompthub/` — local runtime/application data outside the repo; inspect carefully before modifying.

## Important paths

- Repo root: `~/prompthub`
- Docs root: `~/prompthub/docs`
- Agent guide root: `~/prompthub/docs/agent-guides`
- Scripts root: `~/prompthub/scripts`
- Shared enhancement rules: `~/prompthub/app/configs/enhancement-rules.json`
- Local app  `~/.local/share/prompthub/`

## Working assumptions

- Prefer editing source files or generators instead of patching generated outputs directly.
- Treat PromptHub as the source of truth for MCP server sharing and centralized client configuration.
- Preserve supported client compatibility unless the task explicitly allows a breaking change.
- Keep Claude-primary and OpenCode/LM Studio-backup workflows aligned wherever practical.
- Prefer repo wrapper commands in `scripts/` when they exist and accurately represent the intended workflow.

## Before broad changes

Read these first when relevant:

- `docs/architecture/README.md`
- `docs/architecture/ADR-004-modular-monolith.md`
- `docs/architecture/ADR-009-orchestrator-agent.md`
- `docs/guides/06-client-configuration-guide.md`
- `docs/modules/servers.md`
- `scripts/README.md`

## Change strategy

- For config-related work, inspect `app/configs/` and the docs that describe affected clients.
- For router or transport changes, inspect architecture ADRs before modifying behavior.
- For documentation changes, update both user-facing docs and agent-facing docs when conventions change.
- For workflow or operational command changes, update both the script docs and the related agent guides.
- For cleanup work, do not delete historical or failed config paths unless cleanup is explicitly in scope.
