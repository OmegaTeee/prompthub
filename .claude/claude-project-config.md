# Claude project config

The Claude Code setup for this repo, with the reason for each choice. Update this file whenever `.mcp.json`, `.claude/settings.json`, or anything under `.claude/` changes.

Last reviewed: 2026-11-22.

## Context files

| File | Role |
| --- | --- |
| `AGENTS.md` | Canonical shared contract: architecture, commands, conventions, doc rules. Read by every agent. |
| `CLAUDE.md` | Imports `AGENTS.md` with `@AGENTS.md`, then adds the Claude Code tooling notes. |
| `README.md` | Human overview and quick start. |
| `docs/guides/{getting-started,features,operations}.md` | The only user guides. |

## MCP servers

| Scope | Server | Status | Why |
| --- | --- | --- | --- |
| Project (`.mcp.json`) | `prompthub-bridge` | Enabled (only entry in `enabledMcpjsonServers`; `enableAllProjectMcpServers: false`) | Dogfoods the router as client `claude-code`. Points at the deployed checkout's bridge. Needs the daemon running; the bridge reads only `PROMPTHUB_URL`/`CLIENT_NAME` (plus tuning vars), no token. Tool and model profiles resolve server-side, so the entry pins no `TOOL_DISCLOSURE` or `TIER1_SERVERS`. |
| User (`~/.claude.json`) | `tokensave` | Keep | Primary code-navigation tool, required by the user's global rules. |
| User | `headroom` | Keep | Context compression, required by the user's global rules. |
| User | `serena` | Optional | Overlaps with tokensave. Consider disabling it for this project with `/mcp`. |
| Project (`.mcp.json`) | `oraios/serena`, `headroom`, `fetch_mcp` | VS Code only | Listed for VS Code. Claude Code skips them because they are not in `enabledMcpjsonServers`, and it already has `serena` and `headroom` at user scope. |

`.mcp.json` uses the `mcpServers` key (Claude Code format) and is the single project MCP file for both Claude Code and VS Code; there is no `.vscode/mcp.json`.

## Plugins (`.claude/settings.json` → `enabledPlugins`)

| Plugin | State | Why |
| --- | --- | --- |
| `superpowers` | On | Planning, TDD, debugging, and verification workflows for the refactor. |
| `code-review` | On | PR review. |
| `code-simplifier` | On | Refactor cleanup. |
| `github` | On | PRs and issues through `gh`. |
| `plugin-dev` | Off | The repo contains no Claude plugins. |
| `hookify` | Off | No project hook rules exist. |
| `claude-api` | Off | The router talks to OpenAI-compatible local LLMs, not the Anthropic SDK. |

User-scope plugins (output style, headroom, input-router) are personal preferences and stay as they are. Org/desktop-provisioned plugins (Unity, Shopify, finance, and so on) are not controlled by this repo. Disable them in `/plugin` if their skills clutter sessions.

## Skills, agents, commands

| Path | Contents |
| --- | --- |
| `.claude/skills/hypothesis/` | Property-based testing guidance for pytest. |
| `.claude/agents/code-docs.md` | Doc queue step 2: docstrings, type hints, comments. |
| `.claude/agents/user-manual.md` | Doc queue step 3: updates one of the three guide files. |
| `.claude/commands/wiki-*.md` | `docs/wiki/` maintenance. |

Removed: the eight symlinked skills that pointed into `~/Library/Application Support/CherryStudio/…`. They were machine-specific, and they were either off-topic (`docs-review` is a Metabase style guide; `agentic-workflows` is for gh-aw) or duplicated superpowers and plugin skills (`writing-plans`, `skill-creator`, `code-reviewer`, `pr-creator`, `requirements-gathering`, `find-skills`). The `serena` skill was also removed because tokensave is the mandated navigation tool. `.claude/steering/` was folded into `AGENTS.md`.

## Permissions

`.claude/settings.json` keeps its existing allowlist. Suggested additions that the user can apply (not applied automatically):

```json
"Bash(pytest *)", "Bash(ruff *)", "Bash(mypy *)", "Bash(uvicorn *)",
"Bash(curl http://localhost:9090/*)", "Bash(curl http://127.0.0.1:9090/*)"
```

`.claude/settings.local.json` (untracked) routes the API through a local headroom proxy (`ANTHROPIC_BASE_URL`). This is personal and stays out of git.
