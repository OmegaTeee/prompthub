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
| User guides | `docs/guides/` | Claude Code |
| Developer docs | `docs/` | Claude Code |
| API spec | `docs/api/openapi.yaml` | Claude Code |
| Agent guidance | `.claude/steering/` | Claude Code |
| Project metadata | `CLAUDE.md`, `AGENTS.md`, `CHANGELOG.md` | Claude Code |

### Post-Implementation Documentation Queue

After completing a feature, fix, or structural change, run the following three-step documentation pass before considering the work done. Each step uses a dedicated agent (or inline edits for the changelog). Steps are independent and can run in parallel.

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

#### When to run

| Change type | Step 1 (changelog) | Step 2 (code docs) | Step 3 (user guide) |
|---|---|---|---|
| New feature | Yes | Yes | Yes |
| Bug fix | Yes | If code changed | If user-facing |
| Refactor | If notable | Yes | No |
| Config change | Yes | No | If user-facing |
| Test-only | No | No | No |

#### Quick reference

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

### When to Escalate

If an agent encounters any of these, stop and surface it to the user:

- Conflicting instructions between `CLAUDE.md` and steering docs
- A change that would affect more than 20 files
- Security-sensitive modifications (auth, credentials, audit)
- Removing or renaming a public API endpoint
