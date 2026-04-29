# Qwen Family Overview
Here are the main Qwen entries on LM Studio right now: [lmstudio](https://lmstudio.ai/models/qwen3)

## Core Qwen model pages

- Qwen3 family overview (4B, 30B, 235B, dense + MoE, thinking + non‑thinking): https://lmstudio.ai/models/qwen3 [lmstudio](https://lmstudio.ai/models/qwen3)
- Qwen3.5 family overview (dense + MoE, tool use, vision, reasoning, GGUF, Apache 2.0): https://lmstudio.ai/models/qwen3.5 [lmstudio](https://lmstudio.ai/models/qwen3.5)
- Qwen3-8B (supports `/no_think`, 32k default / 131k max with YaRN, GGUF + MLX variants): https://lmstudio.ai/models/qwen/qwen3-8b [lmstudio](https://lmstudio.ai/models/qwen/qwen3-8b)
- Qwen3.5‑9B (262k context, multimodal, reasoning, tool use, GGUF backend): https://lmstudio.ai/models/qwen/qwen3.5-9b [lmstudio](https://lmstudio.ai/models/qwen/qwen3.5-9b)
- Qwen3.5‑35B‑A3B MoE (35B total, 3B active, VL, tool use, 262k context): https://lmstudio.ai/models/qwen/qwen3.5-35b-a3b [lmstudio](https://lmstudio.ai/models/qwen/qwen3.5-35b-a3b)

## Specialized Qwen variants

- Qwen3‑Coder‑Next model page (LM Studio generic): https://lmstudio.ai/models/qwen3-coder-next [lmstudio](https://lmstudio.ai/models/qwen3-coder-next)
- qwen/qwen3‑coder‑next (80B MoE, ~3B active, tuned for coding agents & tool use, GGUF + MLX): https://lmstudio.ai/models/qwen/qwen3-coder-next [lmstudio](https://lmstudio.ai/models/qwen/qwen3-coder-next)
- Qwen3‑VL (vision‑language series, 2B/4B etc., GGUF + MLX, tool use + vision input): https://lmstudio.ai/models/qwen3-vl [lmstudio](https://lmstudio.ai/models/qwen3-vl)
- Qwen3‑Next‑80B (hybrid attention + high‑efficiency MoE, GGUF): https://lmstudio.ai/models/qwen/qwen3-next-80b [lmstudio](https://lmstudio.ai/models/qwen/qwen3-next-80b)

## Quick model comparison (from these pages)

| Model                        | Type / size                         | Context (native / extended)         | Modality / features                           | Formats      | Link |
|-----------------------------|-------------------------------------|-------------------------------------|-----------------------------------------------|-------------|------|
| Qwen3‑8B                    | Dense 8B                            | 32k default, up to 131k with YaRN   | Thinking + non‑thinking, tool use, reasoning  [lmstudio](https://lmstudio.ai/models/qwen/qwen3-8b) | GGUF, MLX    | https://lmstudio.ai/models/qwen/qwen3-8b |
| Qwen3.5‑9B                  | Dense 9B                            | 262k native                         | Multimodal, reasoning, tool use, VL‑trained  [lmstudio](https://lmstudio.ai/models/qwen/qwen3.5-9b) | GGUF        | https://lmstudio.ai/models/qwen/qwen3.5-9b |
| Qwen3.5‑35B‑A3B             | MoE 35B (3B active)                 | 262k native                         | Vision‑language, tool use, reasoning  [lmstudio](https://lmstudio.ai/models/qwen/qwen3.5-35b-a3b)  | GGUF        | https://lmstudio.ai/models/qwen/qwen3.5-35b-a3b |
| Qwen3‑Coder‑Next            | MoE 80B (≈3B active)                | Noted for long‑horizon reasoning    | Coding‑focused, agents, recovery from failures  [lmstudio](https://lmstudio.ai/models/qwen/qwen3-coder-next) | GGUF, MLX    | https://lmstudio.ai/models/qwen/qwen3-coder-next |
| Qwen3‑VL (2B/4B, others)    | Dense and MoE VL models             | Extended (exact per variant)        | Vision input, document & video understanding  [lmstudio](https://lmstudio.ai/models/qwen3-vl) | GGUF, MLX    | https://lmstudio.ai/models/qwen3-vl |
| Qwen3‑Next‑80B              | Next‑gen MoE 80B                    | Large (noted as high‑efficiency)    | Tool use, hybrid attention, agentic use  [lmstudio](https://lmstudio.ai/models/qwen/qwen3-next-80b) | GGUF        | https://lmstudio.ai/models/qwen/qwen3-next-80b |

If you tell me your target (coding vs general chat vs VL, and VRAM/RAM budget), I can narrow this to specific LM Studio presets and quantizations for your box.
