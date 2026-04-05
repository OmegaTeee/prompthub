# AGENTS.md

Default onboarding context for AI coding agents working in this repository.
Cross-client — Claude Code, OpenCode, and future agentic tools share the same repo contract.

## Why this repo exists

PromptHub is the local MCP router project for sharing MCP servers and centralizing client configurations across multiple AI clients.
The repo preserves a single source of truth for routing behavior, config generation, enhancement logic, and cross-client conventions.
Prefer improving shared abstractions over adding one-off client-specific hacks.

## Agent roles

| Agent | Role | Typical use |
| --- | --- | --- |
| **Claude Code** | Primary high-trust implementer | Architecture, structural changes, nuanced refactors, documentation, broad repo work |
| **OpenCode** | Backup local coding agent | Local-first implementation, terminal workflows, second-pass execution, fallback when Claude is unavailable |
| **Copilot / IDE assist** | Inline helper | Autocomplete, snippets, small local edits, quick chat inside the editor |

All agents follow the same repo conventions unless a task explicitly requires client-specific behavior.

## Supported clients

Per-client directories under `clients/`. Active clients are unprefixed; placeholder/draft clients use a `_` prefix.

| Client | Directory | Strategy | Status |
|---|---|---|---|
| Claude Code | `clients/claude-code/` | symlink | Active |
| Claude Desktop | `clients/claude-desktop/` | symlink | Active |
| Codex | `clients/codex/` | symlink | Active |
| LM Studio | `clients/lm-studio/` | symlink | Active |
| Perplexity Desktop | `clients/perplexity-desktop/` | symlink | Active |
| VS Code + Copilot | `clients/vscode/` | merge | Active |
| Default | `clients/default/` | template | Template |
| Cherry Studio | `clients/_cherry-studio/` | manual | Placeholder |
| JetBrains | `clients/_jetbrains/` | symlink | Placeholder |
| Open WebUI | `clients/_open-webui/` | symlink | Placeholder |
| Raycast | `clients/raycast/` | symlink | Active |
| Zed | `clients/_zed/` | manual | Placeholder |

When editing shared config logic, think in terms of cross-client consistency first and per-client customization second.

## Repo priorities

- Keep PromptHub centralized.
- Preserve compatibility across supported clients unless the task explicitly allows a breaking change.
- Prefer generator/source fixes over manual edits to derived output.
- Keep Claude-primary and OpenCode/LM Studio-backup workflows aligned where practical.
- Update durable docs when conventions, paths, or generated outputs change.

## Important paths

- Repo root: `~/prompthub`
- Docs root: `~/prompthub/docs`
- Agent docs: `~/prompthub/docs/agent-guides`
- Client configs: `~/prompthub/clients/`
- Shared enhancement rules: `~/prompthub/app/configs/enhancement-rules.json`

Read these before large or cross-cutting changes:

- `docs/agent-guides/project-map.md`
- `docs/agent-guides/build-test-verify.md`
- `docs/agent-guides/config-locations.md`
- `docs/architecture/README.md`
- `docs/guides/06-client-configuration-guide.md`

## Steering documents

`.claude/steering/` contains three documents loaded into agent context:

| File | Answers | Updated when |
|------|---------|-------------|
| `product.md` | Why does this exist? What does it do? | Features or scope change |
| `tech.md` | How is it built? What patterns to follow? | Stack or conventions change |
| `structure.md` | Where does code live? What owns what? | Files or modules are added/moved |

Keep these concise. Do not add transient content (task lists, session notes, review checklists).

`.claude/agents/` contains the agent spec files (`code-docs.md`, `user-manual.md`) referenced in the doc queue below.

## Operating rules

- Treat PromptHub as the source of truth for MCP server sharing and centralized client configuration.
- Prefer editing source files, templates, or generators instead of patching generated output directly.
- Do not invent new config shapes or naming conventions when an existing pattern already exists.
- Keep MCP server labels, transport language, and env var names consistent across clients where possible.
- Do not delete historical, failed, or experimental config paths unless cleanup is explicitly in scope.
- For local-model workflows, assume LM Studio is the default local LLM backend unless the task states otherwise.
- If code, docs, and external references disagree, trust the current repository and active docs.

## Commit hygiene

- Each commit stands on its own with a clear message
- Use `Co-Authored-By` trailer when an agent builds on another's work
- One logical change per commit (don't bundle unrelated fixes)
- Follow [Keep a Changelog](https://keepachangelog.com/) categories in `CHANGELOG.md`: Added, Changed, Fixed, Removed
- Add entries under `## [Unreleased]` — one sentence summarizing the user-visible change

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

## Post-implementation documentation queue

After completing a feature, fix, or structural change, run the following three-step documentation pass. Each step uses a dedicated agent (or inline edits for the changelog). Steps are independent and can run in parallel.

```
┌──────────────────┐
│  Implementation  │
│    complete       │
└────────┬─────────┘
         │
         ├──────────────────────────────┐
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐
│ 1. CHANGELOG.md │          │ 2. Code docs        │
│   (inline edit) │          │   (code-docs agent) │
└────────┬────────┘          └──────────┬──────────┘
         │                              │
         │          ┌───────────────────┘
         │          │
         ▼          ▼
    ┌──────────────────────┐
    │ 3. User guide        │
    │   (user-manual agent)│
    └──────────────────────┘
```

**Step 1 — Update CHANGELOG.md** (always, inline)

Add a line under `## [Unreleased]` in the appropriate category (Added / Changed / Fixed / Removed). One sentence summarizing the user-visible change, key details in parentheses.

**Step 2 — Update code documentation** (when code was added or modified)

Run the `code-docs` agent on all new or modified files. Scope:
- Docstrings for new/changed functions, classes, and modules
- Type hints on new signatures
- Clarifying comments on non-obvious logic

Do not touch unchanged code. Match the existing style (concise docstrings, 88-char line limit).

**Step 3 — Add or update user guide** (when a user-facing feature was added or changed)

Run the `user-manual` agent to create or update a guide in `docs/guides/`. Scope:
- New feature → new guide file (follow the `NN-name-guide.md` numbering convention)
- Changed feature → update the existing guide in-place (add sections, don't remove working content)
- Include: overview, setup/prerequisites, usage with copy-pasteable examples, troubleshooting

Skip this step for internal-only changes (refactors, test-only changes, CI tweaks).

### When to run

| Change type | Step 1 (changelog) | Step 2 (code docs) | Step 3 (user guide) |
|---|---|---|---|
| New feature | Yes | Yes | Yes |
| Bug fix | Yes | If code changed | If user-facing |
| Refactor | If notable | Yes | No |
| Config change | Yes | No | If user-facing |
| Test-only | No | No | No |

### Quick reference

```bash
# After implementing a feature, run the doc queue:

# 1. Changelog — edit directly
#    Add entry under [Unreleased] → Added/Changed/Fixed/Removed

# 2. Code docs — delegate to agent
#    Agent: code-docs
#    Prompt: "Update docs for new/modified files: <list files>"

# 3. User guide — delegate to agent
#    Agent: user-manual
#    Prompt: "Add/update guide in docs/guides/ for <feature>"
```

## When to escalate

If an agent encounters any of these, stop and surface it to the user:

- Conflicting instructions between `CLAUDE.md` and steering docs
- A change that would affect more than 20 files
- Security-sensitive modifications (auth, credentials, audit)
- Removing or renaming a public API endpoint

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
