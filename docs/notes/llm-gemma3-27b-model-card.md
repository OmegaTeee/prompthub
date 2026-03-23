---
title: "Model Card: gemma3:27b — High-Quality Enhancement Model"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [llm, gemma3, model-card, enhancement, vision, claude-desktop]
---

# gemma3:27b

Google's 27.4B dense transformer. The high-quality enhancement model reserved for Claude Desktop, where prompt clarity has the highest payoff.

## Ollama Manifest

```
Architecture:     gemma3 (dense transformer)
Parameters:       27.4B
Quantization:     Q4_K_M
Disk Size:        17 GB
Context Window:   131,072 tokens
Embedding Length:  5,376
Digest:           a418f5838eaf
License:          Google Gemma Terms of Use
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | Yes | |
| Tool calling | No | No native tool tokens; same limitation as gemma3:4b |
| Thinking mode | No | |
| Vision | Yes | SigLIP vision encoder — stronger visual reasoning than 4b |
| Embeddings | No | Use `bge-m3` instead |

## Ollama Parameters

| Parameter | Value | Notes |
|---|---|---|
| `temperature` | 1.0 | Default; PromptHub overrides to 0.3 for claude-desktop |
| `top_k` | 64 | |
| `top_p` | 0.95 | |
| `stop` | `<end_of_turn>` | Gemma chat format |

## PromptHub Roles

### 1. Claude Desktop Enhancement

**File**: [configs/enhancement-rules.json](../../app/configs/enhancement-rules.json) — `clients.claude-desktop`

| Setting | Value |
|---|---|
| Temperature | 0.3 |
| Max tokens | 600 |
| Privacy | `local_only` |
| System prompt | Structured for reasoning AI, Markdown formatting |

Claude Desktop is the primary reasoning client (routes to Anthropic's API). Enhancement quality matters most here because the rewritten prompt directly influences Claude's output. The 27B model produces more nuanced, better-structured rewrites than `gemma3:4b`.

### 2. Fallback Chain (second position)

```
gemma3:4b → gemma3:27b → null (pass-through)
```

If `gemma3:4b` fails for any client, `gemma3:27b` is tried before giving up. This means even Raycast and VS Code get high-quality enhancement as a fallback.

## Recommendations

- **Loading costs**: At 17 GB, this model will likely evict the orchestrator (`qwen3:14b`) or `gemma3:4b` from VRAM when loaded. Expect a cold-start delay of 10–20 seconds on first Claude Desktop request after other models have been active.
- **Don't use for tool calling**: Same Gemma3 limitation as 4b — no native tool tokens.
- **Vision capability**: Strongest vision model in the local stack. If you enable image analysis in Open WebUI or ComfyUI, this is the model to route to.
- **Context window** (131K) is 3x larger than `qwen3:14b` (40K). Better suited for long-document enhancement or RAG-augmented prompts.
- **Not assigned to most clients** intentionally — the 4b model handles high-frequency, low-latency enhancement while 27b is reserved for the client where quality matters most.
