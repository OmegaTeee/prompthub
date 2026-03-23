# Notes

Working notes, research, model evaluations, and improvement plans that aren't yet formal guides or architecture docs. This is a low-ceremony space for capturing ideas and analysis.

## Folder Structure

```
docs/notes/
├── models/       LLM model cards (one per Ollama model)
├── servers/      MCP server cards (one per registered server)
├── research/     Comparisons, evaluations, stack inventories
├── plans/        Roadmaps and phased improvement proposals
├── dashboard/    Dashboard refactor and observability ideas
└── README.md     This file
```

## Naming Convention

Use a **category prefix** followed by a descriptive topic:

| Prefix | Use for | Location | Examples |
|---|---|---|---|
| `llm-` | Model cards, evaluations | `models/`, `research/` | `llm-qwen3-14b-model-card.md` |
| `mcp-` | MCP server cards | `servers/` | `mcp-context7.md` |
| `plan-` | Roadmaps, phased proposals | `plans/` | `plan-rag-improvement.md` |
| `idea-` | Brainstorming, feature ideation | `dashboard/` or root | `idea-dashboard-improvements.md` |
| `eval-` | Benchmarks, integration tests | `research/` | `eval-mcp-bridge-latency.md` |

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

### models/ — LLM Model Cards

| File | Status | Model | PromptHub Role |
|---|---|---|---|
| `llm-qwen3-14b-model-card.md` | final | qwen3:14b (14.8B) | Orchestrator + OpenClaw primary |
| `llm-gemma3-4b-model-card.md` | final | gemma3:4b (4.3B) | Default enhancement (6 clients) |
| `llm-gemma3-27b-model-card.md` | final | gemma3:27b (27.4B) | Claude Desktop enhancement |
| `llm-qwen3-coder-30b-model-card.md` | final | qwen3-coder:30b (30.5B MoE) | Claude Code enhancement |
| `llm-bge-m3-model-card.md` | final | bge-m3 (567M) | Embeddings (future RAG) |

### servers/ — MCP Server Cards

| File | Status | Auto-start | Key Role |
|---|---|---|---|
| `mcp-context7.md` | final | Yes | Library documentation fetching |
| `mcp-desktop-commander.md` | final | Yes | File operations, terminal, editing (26 tools) |
| `mcp-sequential-thinking.md` | final | Yes | Step-by-step reasoning and planning |
| `mcp-memory.md` | final | Yes | Knowledge graph persistence |
| `mcp-duckduckgo.md` | final | Yes | Web search (no API key needed) |
| `mcp-obsidian-mcp-tools.md` | final | Yes | Obsidian vault operations (keyring auth) |
| `mcp-chrome-devtools.md` | final | No | CDP debugging, profiling (30+ tools) |
| `mcp-browsermcp.md` | final | No | Chrome extension browser automation |

### research/ — Evaluations & Inventories

| File | Status | Description |
|---|---|---|
| `llm-stack.md` | review | Full stack inventory, per-client assignments, experimentation log |
| `llm-mcp-guide.md` | review | 4-model comparison (qwen3/gemma3) for MCP and desktop clients |

### plans/ — Roadmaps

| File | Status | Description |
|---|---|---|
| `plan-rag-improvement.md` | draft | 4-phase RAG improvement roadmap (session context, PGVector, RAG enhancement, n8n) |

### dashboard/ — Dashboard & Observability Ideas

| File | Status | Description |
|---|---|---|
| `idea-dashboard-update.md` | draft | Server control buttons, auto-start changes |
| `idea-dashboard-improvements.md` | draft | UX improvements — loading indicators, toast notifications |
| `idea-dashboard-refactor-recommendations.md` | draft | Refactor suggestions from enhancement middleware work |
| `idea-dashboard-refactor-review.md` | draft | Scoping review for dashboard redesign |
| `idea-dashboard-refactor-tech-overview.md` | draft | Tech stack evaluation — Grafana, Prometheus, OpenTelemetry |
| `idea-grafana-readme.md` | draft | Grafana dashboard import/setup instructions |
| `idea-grafana-dashboard.json` | — | Grafana dashboard JSON definition (import-ready) |
