---
title: "Model Card: qwen3:14b — Orchestrator & Tool-Calling Agent"
status: final
created: 2026-03-08
updated: 2026-03-23
tags: [llm, qwen3, model-card, orchestrator, tool-calling]
---

# qwen3:14b

Alibaba's 14.8B dense transformer. Primary orchestrator model and the minimum viable model for reliable tool-calling through the PromptHub bridge.

## Ollama Manifest

```
Architecture:     qwen3 (dense transformer)
Parameters:       14.8B
Quantization:     Q4_K_M
Disk Size:        9.3 GB
Context Window:   40,960 tokens
Embedding Length:  5,120
Digest:           bdbd181c33f2
License:          Apache 2.0
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | Yes | |
| Tool calling | Yes | Native Qwen3 tool tokens — structured JSON function calls |
| Thinking mode | Yes | `/think` for chain-of-thought, `/no_think` for fast single-turn |
| Vision | No | Text only |
| Embeddings | No | Use `bge-m3` instead |

## Ollama Parameters

| Parameter | Value | Notes |
|---|---|---|
| `temperature` | 0.6 | Default; PromptHub overrides to 0.1 for orchestrator |
| `top_k` | 20 | |
| `top_p` | 0.95 | |
| `repeat_penalty` | 1.0 | |
| `stop` | `<\|im_start\|>`, `<\|im_end\|>` | ChatML format |

## PromptHub Roles

### 1. Orchestrator Agent (primary role)

**File**: [router/orchestrator/agent.py](../../app/router/orchestrator/agent.py) — hardcoded `MODEL = "qwen3:14b"`

Classifies every incoming prompt into an intent category and suggests MCP servers before the prompt reaches the enhancement layer.

| Setting | Value | Why |
|---|---|---|
| Temperature | 0.1 | Deterministic structured output |
| Max tokens | 300 | Only produces JSON |
| Timeout | 2.5s | Must not block enhancement |
| Circuit breaker | 3 failures → 30s recovery | Independent from enhancement |
| LRU cache | 256 entries | Skip repeated prompts |

**Intent categories**: `code`, `documentation`, `search`, `memory`, `workflow`, `reasoning`, `general`

**Fail-safe**: Any error or timeout returns the original prompt unchanged — the orchestrator never blocks the pipeline.

### 2. OpenClaw Primary Model

**File**: [~/.openclaw/openclaw.json](~/.openclaw/openclaw.json) — `agents.defaults.model.primary`

OpenClaw's default model for chat and tool-calling via the PromptHub stdio bridge. Chosen because native tool tokens work reliably with minified schemas (tested; 8B models fail at this).

### 3. Enhancement (not assigned)

Not used for prompt enhancement. Could serve as a fallback enhancement model if added to `enhancement-rules.json`, but `gemma3:4b` is faster for that role and `gemma3:27b` is higher quality.

## Recommendations

- **Keep warm**: This model runs on nearly every request (orchestrator). Ollama will typically keep it loaded alongside `gemma3:4b` (~13 GB combined).
- **Don't reduce to 8B**: Testing showed `qwen3:8b` cannot reliably call tools through the bridge's minified schemas. 14B is the floor for tool-calling.
- **Context window is the smallest** in the stack (40K vs 128K+ for others). Not suitable for long-document tasks — use `gemma3:27b` or `qwen3-coder:30b` for those.
- **Thinking mode**: The orchestrator uses `/no_think` implicitly (low temperature, tight timeout). For other uses where you want chain-of-thought reasoning, enable `/think` explicitly.
