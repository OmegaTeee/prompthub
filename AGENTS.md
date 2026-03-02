# Multi-Agent Contribution Workflow

Rules for AI agents (Claude Code, Copilot) contributing to this project.

## Roles

| Agent           | Role                | Scope                                                 |
|-----------------|---------------------|-------------------------------------------------------|
| **Claude Code** | Primary implementer | Structural changes, new features, bulk edits, commits |
| **Copilot**     | Inline assist       | Autocompletions, snippet generation, chat within IDE  |

Copilot auto-loads `.github/copilot-instructions.md` (thin pointer to CLAUDE.md) and `.github/instructions/*.md` for context.

## Rules

### No Residual Artifacts

Review findings are applied directly as commits. Do not create tracking documents (task lists, review notes, TODO files) in the repository. If a fix is worth making, make it. If it's not, skip it.

Rationale: Tracking files accumulate, go stale, and add noise to the steering context.

### Commit Hygiene

- Each commit stands on its own with a clear message
- Use `Co-Authored-By` trailer when an agent builds on another's work
- One logical change per commit (don't bundle unrelated fixes)

### Steering Documents

`.claude/steering/` contains three documents:

| File | Answers | Updated when |
|------|---------|-------------|
| `product.md` | Why does this exist? What does it do? | Features or scope change |
| `tech.md` | How is it built? What patterns to follow? | Stack or conventions change |
| `structure.md` | Where does code live? What owns what? | Files or modules are added/moved |

These files are loaded into agent context. Keep them concise. Do not add transient content (task lists, session notes, review checklists).

### CHANGELOG.md

- `[Unreleased]` collects changes between releases
- Follow [Keep a Changelog](https://keepachangelog.com/) categories: Added, Changed, Fixed, Removed

### Documentation Location

| Content | Location | Owner |
|---------|----------|-------|
| User guides | `app/docs/guides/` | Claude Code |
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
