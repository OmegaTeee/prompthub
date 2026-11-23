# CLAUDE.md

Project conventions, architecture, commands, and doc rules are shared with other agents in AGENTS.md:

@AGENTS.md

The rest of this file is Claude Code–specific. The active tool setup and the reasons behind it are recorded in [.claude/claude-project-config.md](.claude/claude-project-config.md).

## Tooling in this project

- **Code navigation:** use the tokensave MCP tools (`tokensave_context`, `tokensave_search`, `tokensave_callers`, `tokensave_impact`); the index lives in `.tokensave/`. Don't spawn Explore agents for code research.
- **Project MCP server:** `prompthub-bridge` is the only project server Claude Code loads (`enabledMcpjsonServers`). Root `.mcp.json` is shared with VS Code, which also starts the `serena`, `headroom`, and `fetch_mcp` entries listed there. The bridge dogfoods the router as client `claude-code` and needs the router daemon running on `:9090`. The bridge itself takes no token (bearer keys gate only `/v1/*`).
- **Plugins:** `superpowers`, `code-review`, `code-simplifier`, `github`. Plugins that don't serve this codebase are switched off in `.claude/settings.json`.
- **Project skill:** `hypothesis` (property-based tests for `app/tests`).
- **Project agents:** `code-docs` and `user-manual` (doc queue steps 2 and 3).
- **Commands:** `/wiki-add`, `/wiki-find`, `/wiki-lint`, `/wiki-log` for `docs/wiki/`.

## Doc queue: active directive

After any feature, fix, or structural change, check the doc-queue table in AGENTS.md and ask the user: *"Should I run the doc queue? Based on this change I'd update: [applicable steps]."* Don't skip this question, and don't wait for the user to bring it up.

## Using the bridge's MCP tools

| Situation | What to do |
| --- | --- |
| Server with `auto_start: false` (`chrome-devtools-mcp`) | Start it with `prompthub_start_server` or `curl -X POST http://localhost:9090/servers/{name}/start`, then reload tools. |
| Progressive disclosure hides a server's tools | Call `discover_tools` / `load_server_tools` from the bridge. |
| `comet_*` tools | Need the Comet browser. `comet_connect` launches it; the first connection takes 5–10s. |
