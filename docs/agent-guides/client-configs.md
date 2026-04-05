# Client configs

This guide explains how coding agents should approach supported client configurations in PromptHub.
The goal is to keep configuration behavior centralized, understandable, and consistent across clients.

## Supported-now clients

Current supported-now clients include:

- `vscode-mcp`
- `perplexity-desktop-mcp`
- `claude-code-mcp`
- `claude-desktop-mcp`
- `lm-studio-mcp`
- `raycast-mcp`

Treat this list as the current compatibility surface when making shared config changes.

## Core rules

- Prefer shared config generation patterns over one-off manual client files.
- Keep naming, server labels, and env var references consistent across clients where possible.
- If a client needs a special projection or field mapping, keep the special logic isolated and well documented.
- Avoid introducing a new config shape unless an existing abstraction clearly cannot support it.
- When changing output shape, document user-visible impact and migration expectations.

## Generated versus manual

Before editing any client config:

1. Determine whether the file is generated, templated, or manually maintained.
2. If it is generated, edit the generator or source template instead of only patching the output.
3. If it is manual, preserve existing conventions unless the task explicitly calls for a redesign.
4. If unsure, inspect adjacent docs and implementation files before editing.

## Cross-client consistency

When changing shared config behavior, check for the following:

- Does the same server have the same label across clients where feasible?
- Are transport terms used consistently?
- Do environment variables follow the same names and semantics?
- Does client-specific customization stay small and explainable?
- Are docs and examples still accurate for affected clients?

## Backup workflow alignment

PromptHub should support both Claude-primary and OpenCode/LM Studio-backup workflows without forcing the repo into two different mental models.
When changing shared config logic, prefer conventions that keep those workflows aligned.

That means:

- Shared MCP server definitions should remain central.
- Client-specific differences should stay thin.
- Local-model assumptions should default to LM Studio unless the task says otherwise.
- Agent instructions should remain cross-client when possible.

## Documentation expectations

Update docs when any of the following change:

- Supported client list.
- Config field meanings.
- Output structure.
- Setup steps for a client.
- Shared naming conventions.

Relevant docs may include:

- `docs/guides/06-client-configuration-guide.md`
- `docs/agent-guides/config-locations.md`
- `docs/agent-guides/mcp-routing.md`
- `AGENTS.md`

## Output expectations

In the final summary for client-config work, include:

- Which clients were affected.
- Whether the change touched source templates, generators, or generated outputs.
- Any migration or compatibility concerns.
- Which docs were updated.
