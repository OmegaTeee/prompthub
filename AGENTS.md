# Multi-Agent Contribution Workflow

Rules for AI agents (Claude Code, Cursor/Qwen, Copilot) contributing to this project.

## Roles

| Agent             | Role                | Scope                                                 |
|-------------------|---------------------|-------------------------------------------------------|
| **Claude Code**   | Primary implementer | Structural changes, new features, bulk edits, commits |
| **Cursor (Qwen)** | Reviewer / polish   | Consistency checks, minor fixes, style alignment      |
| **Copilot**       | Inline assist       | Autocompletions, snippet generation within IDE        |

## Workflow

```
1. Implement   — Claude Code writes code, creates/modifies files
2. Commit      — Claude Code commits with descriptive message
3. Review      — Cursor/Qwen reviews the commit, produces patch
4. Apply       — Cursor/Qwen commits fixes directly (no task file)
5. Verify      — Claude Code confirms clean state on next session
```

## Rules

### No Residual Artifacts

Review findings are applied directly as commits. Do not create tracking documents (task lists, review notes, TODO files) in the repository. If a fix is worth making, make it. If it's not, skip it.

Rationale: Tracking files accumulate, go stale, and add noise to the steering context.

### Commit Hygiene

- Each agent's commit stands on its own with a clear message
- Use `Co-Authored-By` trailer when an agent builds on another's work
- One logical change per commit (don't bundle unrelated fixes)
- Never amend another agent's commit; always create a new one

### File Boundaries

Agents should not fight over the same file in the same session. If Claude Code just modified `openapi.yaml`, Cursor reviews it in a separate commit afterward — not concurrently.

### Steering Documents

`.claude/steering/` contains three documents:

| File | Answers | Updated when |
|------|---------|-------------|
| `product.md` | Why does this exist? What does it do? | Features or scope change |
| `tech.md` | How is it built? What patterns to follow? | Stack or conventions change |
| `structure.md` | Where does code live? What owns what? | Files or modules are added/moved |

These files are loaded into agent context. Keep them concise. Do not add transient content (task lists, session notes, review checklists).

### CHANGELOG.md

- `[Unreleased]` stays empty between releases
- Agents add entries under the current version section
- Follow [Keep a Changelog](https://keepachangelog.com/) categories: Added, Changed, Fixed, Removed

### Documentation Location

| Content | Location | Owner |
|---------|----------|-------|
| User guides | `~/Vault/PromptHub/` (Obsidian) | Manual / Cursor |
| Developer docs | `app/docs/` | Claude Code |
| API spec | `app/docs/api/openapi.yaml` | Claude Code |
| Agent guidance | `.claude/steering/` | Claude Code |
| Project metadata | `CLAUDE.md`, `AGENTS.md`, `CHANGELOG.md` | Claude Code |

### When to Escalate

If an agent encounters any of these, stop and surface it to the user:

- Conflicting instructions between `CLAUDE.md` and steering docs
- A change that would affect more than 20 files
- Security-sensitive modifications (auth, credentials, audit)
- Removing or renaming a public API endpoint
