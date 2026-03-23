---
title: "Model Card: qwen3-coder:30b — Code Enhancement Specialist"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [llm, qwen3-coder, model-card, enhancement, coding, moe]
---

# qwen3-coder:30b

Alibaba's 30.5B Mixture-of-Experts code specialist. Only ~3.3B parameters are active per token (16 experts, 2 active), making it significantly faster than its parameter count suggests. Assigned to Claude Code enhancement.

## Ollama Manifest

```
Architecture:     qwen3moe (Mixture-of-Experts)
Parameters:       30.5B total (~3.3B active per token)
Quantization:     Q4_K_M
Disk Size:        18 GB
Context Window:   262,144 tokens
Embedding Length:  2,048
Digest:           06c1097efce0
License:          Apache 2.0
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | Yes | Code-optimized — trained on code repos, documentation, issues |
| Tool calling | Yes | Native Qwen3 tool tokens (requires Ollama ≥ v0.12.1) |
| Thinking mode | No | Non-thinking optimized — designed for fast code generation |
| Vision | No | Text only |
| Embeddings | No | Use `bge-m3` instead |

## Ollama Parameters

| Parameter | Value | Notes |
|---|---|---|
| `temperature` | 0.7 | Default; PromptHub overrides to 0.2 for claude-code |
| `top_k` | 20 | |
| `top_p` | 0.8 | More focused than Gemma3's 0.95 |
| `repeat_penalty` | 1.05 | Slight penalty to avoid code repetition |
| `stop` | `<\|im_start\|>`, `<\|im_end\|>`, `<\|endoftext\|>` | ChatML + EOS |

## PromptHub Roles

### 1. Claude Code Enhancement

**File**: [configs/enhancement-rules.json](../../app/configs/enhancement-rules.json) — `clients.claude-code`

| Setting | Value |
|---|---|
| Temperature | 0.2 |
| Max tokens | 600 |
| Privacy | `local_only` |
| System prompt | Code-precise, include language/framework/file paths if implied |

Claude Code is a CLI tool that generates and modifies code. Enhancement rewrites the user's prompt to be more actionable for a code-generation AI — adding specificity about language, framework, file paths, and intent that the user may have left implicit.

### 2. Potential Tool-Calling Agent

Has native Qwen3 tool tokens like `qwen3:14b`, so it can drive MCP tools through the bridge. Not currently assigned to any tool-calling client, but could serve OpenClaw or Open WebUI for code-heavy workflows where the 256K context window is valuable (e.g., multi-file analysis).

## MoE Architecture Notes

Unlike the dense models in this stack, `qwen3-coder:30b` uses Mixture-of-Experts:

| Property | Value |
|---|---|
| Total experts | 16 |
| Active experts per token | 2 |
| Active parameters per token | ~3.3B |
| Speed | ~10x faster than a dense 30B model |

This means inference speed is closer to a 4B model than a 30B model, despite having 30.5B total parameters. The trade-off is disk and VRAM — the full 18 GB must be loaded even though only a fraction is active per token.

## Recommendations

- **Loading costs**: At 18 GB, this is the largest model in the stack. Loading it will evict most other models from VRAM. Best suited for bursty usage (Claude Code sessions) rather than always-on.
- **Context window** (262K) is the largest in the stack — 6x larger than `qwen3:14b`. Ideal for prompts involving large code contexts, multi-file diffs, or RAG-augmented code review.
- **MoE speed advantage**: Despite being 18 GB on disk, actual inference is fast because only ~3.3B params are active per token. Don't let the disk size deter you from using it.
- **Not in the fallback chain**: If this model fails for Claude Code, enhancement falls back to the global chain (`gemma3:4b → gemma3:27b → null`), not to another code-specific model.
- **Ollama version**: Requires Ollama ≥ v0.12.1 for native tool support. Older versions may silently ignore tool calls.
