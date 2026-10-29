# Notes

This folder holds current working notes that are still useful to the active codebase.

Historical plans, dashboard ideas, and long-dead TODO trackers have been moved to
[docs/archive/README.md](../archive/README.md) so the live docs stop acting like an active roadmap.

## Current scope

Keep notes here only when they still help explain the current product or runtime:

- model cards and local model inventories
- MCP server cards
- active research and evaluation notes
- operational references that are still current

## Naming

Use a category prefix followed by a descriptive topic:

- `llm-` for model cards and evaluations
- `mcp-` for MCP server cards
- `eval-` for benchmarks and comparisons
- `plan-` only for active, near-term work that is still actionable

## Frontmatter

Use YAML frontmatter for every note:

```yaml
---
title: "Human-readable title"
status: draft | review | final
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [relevant, topic, tags]
---
```

## Active content

The live notes set should stay narrow. If a note is only historical context, a dead plan,
or a superseded design idea, archive it instead of leaving it visible as active work.
