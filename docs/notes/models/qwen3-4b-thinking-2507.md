---
title: "Model Card: qwen3-4b-thinking-2507 — Orchestrator / Reasoning Model"
status: active
created: 2026-03-28
updated: 2026-03-28
tags: [llm, qwen3, model-card, orchestrator, reasoning, lm-studio]
---

# qwen3-4b-thinking-2507

Qwen3 4B Thinking (July 2025 release). Chain-of-thought reasoning variant of Qwen3 4B. Used as the orchestrator model for intent classification — classifies incoming prompts, suggests tools, and annotates for the enhancement layer.

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
| Tool calling | Yes | Trained for tool use |
| Thinking mode | Yes | Built-in CoT reasoning head |
| Vision | No | |
| Embeddings | No | |

## LM Studio Configuration

| Parameter | Value | Notes |
|---|---|---|
| Variant | `qwen3-4b-thinking-2507@4bit` | 4-bit quantization via MLX |
| Keep loaded | Yes | Both 4B models stay resident (~5 GB total) |
| Reasoning | LM Studio surfaces thinking in `message.reasoning` field (v0.3.23+) |

## PromptHub Roles

### 1. Orchestrator Agent (intent classification)

**File**: `app/router/orchestrator/agent.py` — `MODEL = "qwen3-4b-thinking-2507"`

Sits upstream of EnhancementService. For each incoming prompt:

1. Classifies intent (code, research, creative, system, general)
2. Suggests relevant MCP tools based on intent
3. Annotates the prompt with routing hints

Configuration:

| Parameter | Value | Notes |
|---|---|---|
| Temperature | 0.1 | Low randomness for reliable structured JSON output |
| Max Tokens | 300 | Only needs to produce a small JSON classification |
| Timeout | 2.5s | Hard ceiling — must not block the enhancement pipeline |
| Circuit Breaker | Separate from enhancement | 3 failures → OPEN, 30s recovery |

### 2. Fallback Chain (second position)

```
qwen3-4b-instruct-2507 → qwen3-4b-thinking-2507 → null (pass-through)
```

If the default enhancement model fails, the thinking variant is tried before falling through to pass-through.

### 3. Cloud Fallback Mapping

**File**: `app/configs/cloud-models.json` — `local_models`

| Cloud Upgrade | Cloud Equivalent |
|---|---|
| `deepseek/deepseek-r1-0528` (free) | `deepseek/deepseek-r1-distill-qwen-14b` |

## Reasoning Behavior

Unlike the standard `qwen3-4b-2507`, this model produces chain-of-thought reasoning before its final answer. In LM Studio's API:

- **Non-streaming**: Reasoning appears in `choices[0].message.reasoning`
- **Streaming**: Reasoning appears in `choices[0].delta.reasoning`

PromptHub's orchestrator extracts only the final JSON answer from `message.content`, ignoring the reasoning trace. The reasoning is useful for debugging via `lms log stream --source model --filter output`.

## Recommendations

- **Keep pre-loaded**: Same 2.5 GB footprint as the standard variant. Both fit in memory simultaneously.
- **Don't use for enhancement**: The thinking overhead adds latency. Use `qwen3-4b-2507` for fast prompt rewrites.
- **Future reasoning lane**: The enhancement sketch (`lm-studio-enhancement-sketch.md`) proposes using this model for prompts that request "step by step" reasoning, opt-in via trigger phrases.

### References
https://huggingface.co/lmstudio-community/Qwen3-4B-Thinking-2507-GGUF
https://lmstudio.ai/models/qwen/qwen3-4b-thinking-2507
