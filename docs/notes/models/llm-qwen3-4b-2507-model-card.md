---
title: "Model Card: qwen/qwen3-4b-2507 — Default Enhancement Model"
status: active
created: 2026-03-28
updated: 2026-03-28
tags: [llm, qwen3, model-card, enhancement, lm-studio]
---

# qwen/qwen3-4b-2507

Qwen3 4B Instruct (July 2025 release). Default enhancement model for all PromptHub clients. Fast instruction-following without thinking mode — designed for prompt rewrites, clarification, and formatting.

## LM Studio Manifest

```
Engine:           mlx-llm v1.4.0 (Apple Metal)
Architecture:     qwen3 (dense transformer)
Parameters:       4B
Format:           safetensors (MLX)
Quantization:     4-bit
Disk Size:        2.50 GB
Context Window:   262,144 tokens
Trained for Tools: Yes
Vision:           No
Publisher:        qwen (official)
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | Yes | |
| Tool calling | Yes | Trained for tool use; not currently used by enhancement |
| Thinking mode | No | Use `qwen3-4b-thinking-2507` for CoT reasoning |
| Vision | No | |
| Embeddings | No | Use `text-embedding-qwen3-embedding-0.6b` |

## LM Studio Configuration

| Parameter | Value | Notes |
|---|---|---|
| Variant | `qwen/qwen3-4b-2507@4bit` | 4-bit quantization via MLX |
| Keep loaded | Yes | Both 4B models stay resident (~5 GB total) |
| JIT TTL | Default (60 min) | Not relevant — model is pre-loaded |

## PromptHub Roles

### 1. Default Enhancement Model (all clients)

**File**: `app/configs/enhancement-rules.json` — `default.model` and all `clients.*.model`

Rewrites user prompts to be clearer and more specific. Assigned to all 9 clients:

| Client | Temperature | Max Tokens | System Prompt Focus |
|---|---|---|---|
| **default** | 0.3 | 500 | General prompt clarity |
| **claude-desktop** | 0.3 | 600 | Structured for reasoning AI, Markdown |
| **claude-code** | 0.2 | 600 | Precise coding prompts, file paths |
| **vscode** | 0.2 | 500 | Concise code prompts |
| **raycast** | 0.3 | 300 | Action-oriented, CLI-style, <150 words |
| **perplexity** | 0.3 | 400 | Research questions, Markdown, wikilinks |
| **cursor** | 0.2 | 500 | File-path-aware code prompts |
| **comfyui** | 0.5 | 400 | Image generation prompt expansion |
| **open-webui** | 0.3 | 500 | Conversational clarity |

### 2. Settings Default

**File**: `app/router/config/settings.py` — `llm_model = "qwen/qwen3-4b-2507"`

The `LLM_MODEL` env var defaults to this model.

### 3. Fallback Chain (first position)

```
qwen/qwen3-4b-2507 → qwen/qwen3-4b-thinking-2507 → null (pass-through)
```

### 4. Cloud Fallback Mapping

**File**: `app/configs/cloud-models.json` — `local_models`

| Cloud Upgrade | Cloud Equivalent |
|---|---|
| `meta-llama/llama-3.3-70b-instruct` (free) | `mistralai/mistral-small-3.1-24b-instruct` (free) |

## Recommendations

- **Keep pre-loaded**: At 2.5 GB, this model and its thinking sibling fit comfortably in memory together. No JIT needed.
- **Enhancement is disabled by default** on API keys (`"enhance": false`). Toggle individual keys in `api-keys.json` to activate.
- **Tool calling is available** but not used by the enhancement pipeline. Could be useful for future agentic workflows.
