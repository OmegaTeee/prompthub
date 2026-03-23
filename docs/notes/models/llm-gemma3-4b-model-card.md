---
title: "Model Card: gemma3:4b — Default Enhancement Model"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [llm, gemma3, model-card, enhancement, default]
---

# gemma3:4b

Google's 4.3B dense transformer. The workhorse enhancement model — fast enough to run on every request without noticeable latency, and small enough to stay warm alongside the orchestrator.

## Ollama Manifest

```
Architecture:     gemma3 (dense transformer)
Parameters:       4.3B
Quantization:     Q4_K_M
Disk Size:        3.3 GB
Context Window:   131,072 tokens
Embedding Length:  2,560
Digest:           a2af6cc3eb7f
License:          Google Gemma Terms of Use
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | Yes | |
| Tool calling | No | No native tool tokens; prompt-engineering only, unreliable |
| Thinking mode | No | |
| Vision | Yes | SigLIP vision encoder — can analyze images in chat |
| Embeddings | No | Use `bge-m3` instead |

## Ollama Parameters

| Parameter | Value | Notes |
|---|---|---|
| `temperature` | 1.0 | Default; PromptHub overrides per client (0.2–0.5) |
| `top_k` | 64 | |
| `top_p` | 0.95 | |
| `stop` | `<end_of_turn>` | Gemma chat format |

## PromptHub Roles

### 1. Default Enhancement Model (primary role)

**File**: [configs/enhancement-rules.json](../../app/configs/enhancement-rules.json) — `default.model`

Rewrites user prompts to be clearer and more specific before they reach the downstream AI. Assigned to 6 of 9 clients:

| Client | Temperature | Max Tokens | System Prompt Focus |
|---|---|---|---|
| **default** | 0.3 | 500 | General prompt clarity |
| **vscode** | 0.2 | 500 | Concise code prompts |
| **raycast** | 0.3 | 300 | Action-oriented, CLI-style, <150 words |
| **perplexity** | 0.3 | 400 | Research questions, Markdown, wikilinks |
| **cursor** | 0.2 | 500 | File-path-aware code prompts |
| **comfyui** | 0.5 | 400 | Image generation prompt expansion |
| **open-webui** | 0.3 | 500 | Conversational clarity |

### 2. Fallback Chain (first position)

**File**: [configs/enhancement-rules.json](../../app/configs/enhancement-rules.json) — `fallback_chain`

```
gemma3:4b → gemma3:27b → null (pass-through)
```

If `gemma3:4b` fails, the system tries `gemma3:27b`. If both fail, the original prompt passes through unenhanced.

### 3. Settings Default

**File**: [router/config/settings.py](../../app/router/config/settings.py) — `ollama_model = "gemma3:4b"`

The `OLLAMA_MODEL` env var defaults to `gemma3:4b`, used as the baseline model when no client-specific override applies.

## Recommendations

- **Keep this model**: It loads in under 5 seconds and uses minimal VRAM. Combined with the orchestrator (`qwen3:14b`), the pair fits in ~13 GB — leaving room for larger models when needed.
- **Don't use for tool calling**: Gemma3 lacks native tool tokens. Testing confirmed that small Gemma models fake tool calls or refuse them entirely through the bridge. Use `qwen3:14b` minimum for tool-calling clients.
- **Vision is available** but not used by PromptHub's enhancement pipeline. Could be useful for ComfyUI image-to-prompt workflows in Open WebUI.
- **Enhancement is currently disabled** on all API keys (`"enhance": false`). Toggle individual keys to `true` in `api-keys.json` to activate.
- **Cloud fallback**: Raycast and Perplexity (both `free_ok` privacy) fall back to OpenRouter free-tier when this model's Ollama instance is down.
