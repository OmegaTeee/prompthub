# Three-Track Documentation System

Feature documentation uses three colocated files per feature:

| Track | File | Audience | Purpose |
|-------|------|----------|---------|
| **Tour** | `tour.md` | Developers, AI agents | Testable verification steps (source of truth) |
| **Product** | `product.md` | End users | How to use the feature |
| **Setup** | `setup.md` | Developers | How to configure, run, and debug |

## Workflow

1. **Tour first** — Write the verification tour before anything else
2. **Derive** — Generate product and tech docs from the completed tour
3. **Verify** — Run tour steps against the live system to confirm accuracy
4. **Sync** — When behavior changes, update the tour first, then regenerate

## Using the Skill

The `doc-tour` skill automates this workflow interactively:

```
/doc-tour
```

Templates and full instructions live at `~/.claude/skills/doc-tour/`.

## Output Location

Feature docs are colocated at `docs/features/<feature>/`:

```
docs/features/openai-proxy/
├── tour.md       # Verification steps (source of truth)
├── product.md    # User-facing guide
└── setup.md      # Developer setup
```
