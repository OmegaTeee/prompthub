---
title: "LLM Model Card: qwen3.5:2b — Default Enhancement Model"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [llm, model-card, qwen3.5, enhancement, text-rewriting]
---

# qwen3.5:2b

Alibaba's Qwen3.5 2B — hybrid architecture (Gated Delta Networks + sparse MoE) with thinking toggle. Default enhancement model for 6 of 9 PromptHub clients. Replaced `gemma3:4b` for better instruction-following at lower resource cost.

## Ollama Manifest

| Property | Value |
|---|---|
| Architecture | qwen35 |
| Parameters | 2.3B |
| Quantization | Q8_0 |
| Disk size | 2.7 GB |
| Context length | 262,144 |
| Embedding length | 2,048 |
| Minimum Ollama | v0.17.1 |

## Capabilities

| Capability | Supported |
|---|---|
| Completion | Yes |
| Tool calling | Yes |
| Thinking (hybrid) | Yes — toggle reasoning on/off |
| Vision | Yes |
| Embeddings | No |

## Default Parameters

| Parameter | Value |
|---|---|
| temperature | 1.0 |
| top_k | 20 |
| top_p | 0.95 |
| presence_penalty | 1.5 |

## PromptHub Roles

### Default enhancement model

Assigned to 6 of 9 clients in `enhancement-rules.json`:

| Client | Temperature | Max tokens | Privacy |
|---|---|---|---|
| default | 0.3 | 500 | local_only |
| vscode | 0.2 | 500 | local_only |
| raycast | 0.3 | 300 | free_ok |
| perplexity | 0.3 | 400 | free_ok |
| cursor | 0.2 | 500 | local_only |
| comfyui | 0.5 | 400 | local_only |
| open-webui | 0.3 | 500 | local_only |

**Not used by**: claude-desktop (gemma3:27b), claude-code (qwen3-coder:30b)

### Raycast AI Chat model

Available as `qwen3.5 2b` in Raycast Chat custom provider (`clients/raycast-ai-providers.yaml`). Direct `/v1/chat/completions` access — no enhancement pipeline.

### Fallback chain position

First position: `qwen3.5:2b → gemma3:27b → null`

If qwen3.5:2b fails to load (e.g., Ollama restart), enhancement falls back to gemma3:27b. If both fail, enhancement is skipped (prompt passes through unmodified).

### Settings default

`ollama_model = "qwen3.5:2b"` in `app/router/config/settings.py`. This is the model used when no client-specific override exists.

## Why qwen3.5:2b over gemma3:4b

| Factor | gemma3:4b | qwen3.5:2b |
|---|---|---|
| Parameters | 4.3B | 2.3B |
| Disk | 3.3 GB | 2.7 GB |
| Context | 128K | 256K |
| Instruction following | Adequate | Noticeably better |
| Hybrid thinking | No | Yes |
| Tool calling | No | Yes (native tokens) |
| License | Gemma | Apache 2.0 |

Key advantages: better instruction comprehension for rewriting tasks ("improve writing", "change tone"), smaller footprint, hybrid thinking toggle, and native tool-calling tokens (though tool-calling through the PromptHub bridge still requires ≥14B for reliability with minified schemas).

## Cloud Fallback

When Ollama is unavailable and client privacy allows (`free_ok` or `any`):

| Cloud equivalent | Cloud upgrade |
|---|---|
| `mistralai/mistral-small-3.1-24b-instruct` (free) | `meta-llama/llama-3.3-70b-instruct` (free) |

## VRAM Notes

At 2.7 GB, qwen3.5:2b coexists easily with all other models on Apple Silicon. Lighter than gemma3:4b (3.3 GB), so VRAM pressure is reduced.

## Recommendations

- **Use for**: Text rewriting, tone adjustment, prompt enhancement, simple chat, Raycast prompt commands
- **Do not use for**: Tool-calling through the PromptHub bridge (use qwen3:14b+), deep code generation (use qwen3-coder:30b), complex reasoning tasks
- **Keep gemma3:4b installed**: Still useful as a fallback and for comparison testing
