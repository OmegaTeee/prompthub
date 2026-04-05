---
title: "Model Card: deepseek/deepseek-r1-0528-qwen3-8b — General-Purpose Reasoning Model"
status: active
created: 2026-04-05
updated: 2026-04-05
tags: [llm, deepseek, r1, qwen3, model-card, reasoning, lm-studio]
---

# deepseek/deepseek-r1-0528-qwen3-8b

DeepSeek R1 0528 distilled onto Qwen3 8B. A reasoning model that uses extended chain-of-thought before generating answers. Stronger than the 4B models at complex multi-step tasks, at the cost of higher latency and memory usage.

## LM Studio Manifest

```
Engine:           mlx-llm (Apple Metal)
Architecture:     qwen3 (dense transformer, R1 distillation)
Parameters:       8B
Format:           safetensors (MLX)
Quantization:     4-bit
Context Window:   131,072 tokens
Trained for Tools: Yes
Vision:           No
Publisher:        deepseek-ai (distilled by community)
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | Yes | |
| Tool calling | Yes | Trained for tool use |
| Thinking mode | Yes | Extended CoT reasoning (R1 distillation) |
| Vision | No | |
| Embeddings | No | |

## PromptHub Roles

**None assigned.** This model is available for general use in Cherry Studio and other clients that connect directly to LM Studio. It is not currently wired into the PromptHub enhancement or orchestrator pipelines.

### Potential future roles

- **Orchestrator upgrade**: Could replace `qwen3-4b-thinking-2507` (4B) for intent classification if higher accuracy is needed — the R1 distillation provides stronger reasoning at ~2x the memory cost.
- **Complex enhancement**: Could serve as a premium enhancement model for clients that benefit from deeper prompt analysis (e.g., comfyui image generation prompts).

## Cherry Studio Usage

Available as a direct LM Studio model in Cherry Studio's model selector. No PromptHub proxy needed — Cherry Studio connects to `http://127.0.0.1:1234/v1` directly.

## Recommendations

- **Not pre-loaded by default** — load on demand via LM Studio or Cherry Studio to avoid memory pressure alongside the two 4B enhancement models.
- **R1 distillation trade-off**: Significantly better reasoning than the 4B thinking model, but slower first-token latency due to extended CoT generation. Best suited for tasks where accuracy matters more than speed.
- **8B at 4-bit**: ~5 GB in memory. If loaded alongside both 4B models (~5 GB), total footprint would be ~10 GB.
