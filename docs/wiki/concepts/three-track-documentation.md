---
slug: three-track-documentation
section: concepts
status: archived-to-wiki
related: docs/architecture/*
---
# Three-Track Documentation System

Feature documentation uses three colocated files per feature:

| Track | File | Audience | Purpose |
|-------|------|----------|--------|
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

```bash
# Interactive setup
code-docs doc-tour --feature "new-feature"

# Generate from existing tour
generate-docs-from-tour --tour-path ./features/new-feature/tour.md
```

## Example Structure

```
features/
├── new-feature/
│   ├── tour.md              # Verification steps (source of truth)
│   ├── product.md           # User-facing documentation
│   └── setup.md             # Technical implementation guide
```

**Key principle**: The tour is the only file that must be perfect. Product and Setup docs are generated from it or derived once verified.
