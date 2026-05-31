# Sunset the `clients/<name>/` directory pattern

> **Status (2026-05-31):** Vision-stage idea. No code change planned yet. Captures the thinking after PRs #31–#41 made per-client behavior server-side, which makes the per-client `clients/<name>/` directory pattern mostly redundant.

## What the doc is for

A durable home for the "should we replace bespoke per-client config plumbing with a sync tool?" thought so it doesn't evaporate. Includes the two candidate tools, the architectural reason it's worth considering *now* (and wasn't before), a migration sketch, and the open questions that block a decision.

## Why this is worth considering now

Before PRs #31–#41 (progressive tool disclosure + model/tool profiles), each MCP client needed its own bespoke config block — different `enabled` flags, different `mcpServers` entries, different env vars per client to control behavior. The `clients/<name>/` directory pattern (one folder per client with `setup.sh`, `mcp.json`, `check.sh`, README, sometimes an `llm.txt` knowledge file) made sense because *the per-client divergence was on the client side*.

After PRs #31–#41:
- Per-client tool disclosure → resolved server-side via `tool_profile` in `enhancement-rules.json` and fetched at bridge startup by `GET /clients/{name}/tool-profile`.
- Per-client model selection → resolved server-side via `model_profile` + `model_profiles` in the same config.
- The bridge entry every client needs is functionally identical: `command: node`, `args: [path/to/prompthub-bridge.js]`, `env: { CLIENT_NAME: "<name>" }`.

That uniformity is exactly what generic MCP-sync tools assume.

## Candidate tools

### agentsync ([dallay/agentsync](https://github.com/dallay/agentsync))

- **Model:** Single source of truth in `.agents/`; symlinks created in each client's config location via `agentsync apply`.
- **Coverage:** Claude Code, GitHub Copilot, Gemini CLI, Cursor, VS Code, OpenCode, OpenAI Codex CLI, plus ~32 others (Cline, Windsurf, etc.).
- **Sync mechanism:** Push-based (`agentsync apply`); optional git-hook automation. Source-edits propagate automatically because destinations are symlinks, not copies.
- **Per-client divergence:** Doesn't natively handle per-client env-var variation. Fine for us: post-#31–#41 we *don't want* per-client env-var divergence anymore — the router profile is the source of per-client truth.

### mcp-sync ([ztripez/mcp-sync](https://github.com/ztripez/mcp-sync))

- **Model:** Three-tier hierarchy — `~/.mcp-sync/global.json` synced everywhere; `.mcp.json` per-project overrides; smart merge.
- **Coverage:** Claude Desktop, Claude Code, Cline, Roo, VS Code, Cursor, Continue. Custom clients via `~/.mcp-sync/client_definitions.json`.
- **Sync mechanism:** Smart-merge file copies (not symlinks); dry-run mode to preview.
- **Per-client divergence:** Limited. Same as agentsync, fine post-#31–#41.

### Recommendation

**agentsync.** Symlink model means there's no drift between source and destinations; broader client coverage matches our supported set better; git-hook automation gives a "config-as-code" feel that matches the rest of the repo. The cost is one extra dependency (Rust 1.89+ if building from source, or pip/npm/crates install).

## Migration sketch

Roughly 4 work-units, each independently revertible:

1. **Audit `clients/<name>/`.** Build a disposition table: for each client folder, classify content as (a) `setup.sh`/`check.sh` boilerplate that agentsync replaces, (b) MCP config block that agentsync templatizes from one source, (c) unique non-MCP content like LM Studio presets or per-client `llm.txt` knowledge files. Item (c) is the real work — where does it move?
2. **Extract unique content out of `clients/`.** LM Studio presets → user's LM Studio preset folder (already where the runtime expects them). `llm.txt` knowledge files → either bundled with agentsync's source-of-truth directory or moved to `docs/clients/`. Per-client READMEs → either inlined into `docs/guides/06-client-configuration-guide.md` or kept as `docs/clients/<name>.md`.
3. **Install and configure agentsync.** Create `.agents/prompthub-bridge.json` as the single source of truth for the bridge entry. Document `CLIENT_NAME` as the only per-client env var (everything else lives in `enhancement-rules.json`).
4. **Replace `clients/*/setup.sh` with `agentsync apply`.** Update `docs/guides/06-client-configuration-guide.md` to read "install agentsync, set CLIENT_NAME, run apply." Delete `clients/<name>/` once nothing in the repo references it.

## Open questions (blockers for a decision)

- **Do we actually want zero per-client env-var overrides?** The bridge currently supports `TOOL_DISCLOSURE=full` as an env-pin override of router config (useful for debugging or "this one client should stay full mode"). If we sync the same env block everywhere, we lose per-client override capability. Counter-argument: the override capability exists in `enhancement-rules.json` already, where it belongs.
- **What happens to `clients/dotfiles/shell_common.sh`?** It's loaded into the user's shell, not consumed by an MCP client. Probably stays where it is regardless of which sync tool wins.
- **What's in each `clients/<name>/llm.txt`?** Need to read each to decide whether the content is durable knowledge (keep, move) or stale exploration (delete). The memory note `project_client_llm_txt_pattern` should help here.
- **agentsync coverage**: does it natively support Cherry Studio, Open WebUI, LobeChat, Raycast? Doc lists "32+ additional agents" but I haven't checked the full list — needs verification before committing.

## Next decision (not now)

Either:
- **Pick one client to migrate as a pilot** (suggest `vscode`, since it has the cleanest bespoke config and is the most-used) — measure the actual work, then decide whether to roll out to the rest.
- **Or do the disposition audit first** (Step 1 above) and revisit. Step 1 is information-gathering; it doesn't commit to either tool or a migration.

Recommendation: audit first. Two hours of reading the seventeen `clients/<name>/` folders against the disposition table beats picking a tool blind.

## See also

- The user guide for clients today: [`docs/guides/06-client-configuration-guide.md`](../../guides/06-client-configuration-guide.md).
- The mechanism that made this idea viable: [`docs/architecture/ADR-008-task-specific-models.md`](../../architecture/ADR-008-task-specific-models.md) (per-client model profiles) and the now-merged stack PRs #31, #32, #33 (per-client tool profiles + router-driven resolution).
- The pattern this would replace: every `clients/<name>/setup.sh` script in the repo today.
