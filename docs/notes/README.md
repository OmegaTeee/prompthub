# Notes

Working notes, research, model evaluations, and improvement plans that aren't yet formal guides or architecture docs. This is a low-ceremony space for capturing ideas and analysis.

## Naming Convention

Use a **category prefix** followed by a descriptive topic:

| Prefix | Use for | Examples |
|---|---|---|
| `llm-` | Model evaluations, comparisons, model cards | `llm-qwen3-14b-model-card.md` |
| `plan-` | Roadmaps, improvement plans, phased proposals | `plan-rag-improvement.md` |
| `idea-` | Brainstorming, feature ideation, explorations | `idea-webhook-ingestion.md` |
| `eval-` | Benchmarks, tool evaluations, integration tests | `eval-mcp-bridge-latency.md` |

## Frontmatter

Every note must include YAML frontmatter:

```yaml
---
title: "Human-readable title"
status: draft | review | final
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [relevant, topic, tags]
---
```

**Status lifecycle:**
- **draft** — Work in progress, incomplete, may contain placeholders
- **review** — Content is complete, needs validation or peer review
- **final** — Validated and ready to reference; consider promoting to `docs/guides/` or `docs/architecture/` if broadly useful

## What belongs here vs. elsewhere

| Content type | Location |
|---|---|
| Setup & integration guides | `docs/guides/` |
| Architecture decisions (ADRs) | `docs/architecture/` |
| API specs | `docs/api/` |
| Module documentation | `docs/modules/` |
| Historical/completed docs | `docs/archive/` |
| Everything else (research, plans, model cards, ideas) | `docs/notes/` |

## Current notes

### Model cards

| File | Status | Model | PromptHub Role |
|---|---|---|---|
| `llm-qwen3-14b-model-card.md` | final | qwen3:14b (14.8B) | Orchestrator + OpenClaw primary |
| `llm-gemma3-4b-model-card.md` | final | gemma3:4b (4.3B) | Default enhancement (6 clients) |
| `llm-gemma3-27b-model-card.md` | final | gemma3:27b (27.4B) | Claude Desktop enhancement |
| `llm-qwen3-coder-30b-model-card.md` | final | qwen3-coder:30b (30.5B MoE) | Claude Code enhancement |
| `llm-bge-m3-model-card.md` | final | bge-m3 (567M) | Embeddings (future RAG) |

### Research & plans

| File | Status | Description |
|---|---|---|
| `llm-stack.md` | review | Full stack inventory, per-client assignments, experimentation log |
| `llm-mcp-guide.md` | review | 4-model comparison (qwen3/gemma3) for MCP and desktop clients |
| `plan-rag-improvement.md` | draft | 4-phase RAG improvement roadmap (session context, PGVector, RAG enhancement, n8n) |
