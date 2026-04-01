---
title: Local LLM Recommendations for PromptHub
description: Opinionated guide for choosing local LLMs by role, hardware tier, and quantization level. Covers model families, hardware requirements, and PromptHub-specific setup.
tags: [llm, lm-studio, models, hardware, quantization, setup]
---

# Local LLM Recommendations

PromptHub connects to any OpenAI-compatible local LLM server. This guide helps you pick the right models for your hardware and workflow.

> All models should be run in GGUF format with **Q5_K** or **Q4_K** quantization to ensure compatibility with M3 Max hardware and optimal performance. Use Qwen3 **_8B_** or **_14B_** for most practical workflows, balancing speed, capability, and resource usage.
## Roles

Every recommendation in this guide maps to one of these roles:

| Role | Description | PromptHub Example |
|------|-------------|-------------------|
| **Fast Chat** | Quick responses, prompt rewriting, lightweight tasks | Enhancement model |
| **Reasoning** | Chain-of-thought, planning, intent classification | Orchestrator model |
| **Coding** | Code generation, completion, refactoring | IDE copilot, Claude Code |
| **Assistant** | General-purpose, instruction following | Open WebUI, Claude Desktop |
| **Agent** | Agentic workflows, tool calling, multi-step tasks | MCP tool orchestration |
| **Inline** | Fast completions, tab-complete, fill-in-the-middle | VS Code, Cursor, Zed |
| **Research** | Web search augmentation, summarization | Perplexity, Raycast |
| **Embedding** | Vector search, RAG, semantic similarity | Future RAG pipeline |

---

## 1. Quick Reference

If you just want an answer, use this table. Find your RAM tier and the role you need.

| RAM | Fast Chat | Reasoning | Coding | Assistant | Agent | Inline | Embedding |
|-----|-----------|-----------|--------|-----------|-------|--------|-----------|
| **8 GB** | Qwen3 4B Q4 | Qwen3 4B Thinking Q4 | Qwen3 4B Q4 | Gemma 3 4B Q4 | Qwen3 4B Q4 | Phi-4 Mini 3.8B Q4 | Nomic Embed v1.5 |
| **16 GB** | Qwen3 8B Q4 | Phi-4 14B Q4 | Devstral Small 24B Q3 | Qwen3 8B Q4 | Qwen3 8B Q4 | Qwen3 4B Q6 | Nomic Embed v1.5 |
| **32 GB** | Qwen3 14B Q4 | Qwen3 14B Q4 | Devstral Small 24B Q5 | Qwen3 14B Q4 | Qwen3 14B Q4 | Qwen3 4B Q6 | Qwen3 Embedding 0.6B |
| **64 GB+** | Qwen3 30B Q4 | DeepSeek R1 32B Q6 | Qwen3 Coder 30B Q4 | Llama 3.3 70B Q4 | GPT-OSS 20B Q5 | Qwen3 4B Q8 | Qwen3 Embedding 0.6B |

> All models assume LM Studio with GGUF quantization. Apple Silicon users should prefer the MLX engine.

---

## 2. Model Families

A brief overview of the major families available in LM Studio as of mid-2026.

### Qwen3 / Qwen3.5 (Alibaba)

The best all-rounder family right now. Dense models from 0.6B to 235B, plus MoE variants (e.g., Qwen3.5 A3B). Strong multilingual support, native tool calling, and a thinking mode that toggles chain-of-thought on and off. PromptHub's default models are from this family.

- **Strengths**: Tool calling, multilingual, thinking mode, wide size range
- **Best for**: Fast Chat, Reasoning, Agent, Coding
- **License**: Apache 2.0

### Llama 4 (Meta)

Meta's latest generation. Scout (109B MoE, 17B active) and Maverick (400B MoE, 17B active) are the flagship models. Native vision support and 1M context window. Requires significant RAM for the full models, but the active parameter count is manageable.

- **Strengths**: Long context (1M), vision, open license
- **Best for**: Assistant, Research
- **License**: Llama 4 Community (Apache 2.0 compatible)

### Gemma 3 (Google)

Efficient dense models from 1B to 27B. Vision support across the range. Good balance of quality and resource usage on constrained hardware.

- **Strengths**: Vision at small sizes, efficient inference
- **Best for**: Assistant, Fast Chat on low RAM
- **License**: Gemma Terms of Use (permissive)

### Phi-4 (Microsoft)

Small but punches above its weight. The 3.8B Mini and 14B models deliver strong reasoning for their size. Excellent choice when you need quality in a tight memory budget.

- **Strengths**: Reasoning per parameter, compact
- **Best for**: Reasoning, Inline
- **License**: MIT

### Mistral / Devstral (Mistral AI)

General-purpose Mistral models and the code-specialized Devstral line. Devstral Small (24B) is one of the best open coding models at its size. Larger models (Mistral Large, Mixtral) use MoE.

- **Strengths**: Code generation (Devstral), strong instruction following
- **Best for**: Coding, Assistant
- **License**: Apache 2.0

### DeepSeek R1 / V3 (DeepSeek)

Reasoning-first models. The full R1 is 671B MoE (37B active) -- impractical locally -- but the distilled versions (7B, 14B, 32B, 70B) based on Qwen and Llama backbones bring R1-level reasoning to consumer hardware.

- **Strengths**: Deep reasoning, thinking mode, free API fallback
- **Best for**: Reasoning, Coding (complex problems)
- **License**: MIT

### GPT-OSS (OpenAI)

OpenAI's first open-weight model. 20B dense. Native support in LM Studio. Well-suited for tool calling and agentic workflows given its training lineage.

- **Strengths**: Tool calling, good at following structured output formats
- **Best for**: Agent, Assistant
- **License**: MIT

---

## 3. Quantization Guide

Quantization reduces model size by using fewer bits per weight. Lower bits = smaller file = less RAM, but quality degrades.

| Level | Bits/Weight | Quality | Notes |
|-------|-------------|---------|-------|
| Q2_K | ~2.5 | Poor | Only for extreme memory constraints. Noticeable degradation. |
| Q3_K_M | ~3.5 | Usable | Some quality loss. Good for fitting very large models in limited RAM. |
| **Q4_K_M** | **~4.5** | **Good** | **Recommended default.** Best balance of size and quality. |
| Q5_K_M | ~5.5 | Better | ~15% larger than Q4. Worth it if RAM allows. |
| Q6_K | ~6.5 | Very Good | ~50% larger than Q4. Diminishing returns for most tasks. |
| Q8_0 | 8.0 | Near-original | ~2x size of Q4. For benchmarking or quality-critical tasks. |
| F16/BF16 | 16.0 | Original | Full precision. Use for embedding models and reference testing only. |

### Estimating RAM usage

```
RAM needed = (model_params_in_billions x bits_per_weight) / 8 + 2 GB overhead
```

Examples:
- 7B model at Q4_K_M: `(7 x 4.5) / 8 + 2 = 5.9 GB`
- 14B model at Q4_K_M: `(14 x 4.5) / 8 + 2 = 9.9 GB`
- 30B model at Q4_K_M: `(30 x 4.5) / 8 + 2 = 18.9 GB`

> The 2 GB overhead accounts for KV cache, runtime buffers, and LM Studio itself. Long context or large batch sizes increase this.

---

## 4. Hardware Requirements

All figures assume GGUF format with Q4_K_M quantization unless noted. Apple Silicon unified memory is shared between CPU and GPU -- reserve 4-6 GB for macOS and other apps.

| RAM | Usable for Models | Max Dense Model (Q4) | Recommended Models |
|-----|-------------------|----------------------|-------------------|
| **8 GB** | ~3-4 GB | ~3B | Phi-4 Mini 3.8B, Qwen3 4B, Gemma 3 4B |
| **16 GB** | ~10-12 GB | ~7-8B | Qwen3 8B, Phi-4 14B (Q3), Gemma 3 12B |
| **32 GB** | ~24-26 GB | ~14B | Qwen3 14B, Devstral Small 24B, DeepSeek R1 14B distill |
| **48 GB** | ~40-42 GB | ~30B | Qwen3 30B, Devstral Small 24B (Q6), Mistral Small 24B |
| **64 GB+** | ~56-58 GB | ~70B | Llama 3.3 70B, Qwen2.5 Coder 32B (Q6), DeepSeek R1 32B distill |

**MoE models** have a large total parameter count but only activate a fraction per token. For example, Qwen3.5 A3B (MoE) has ~36B total params but only 3B active -- it needs RAM for all 36B weights but runs at 3B-equivalent speed.

---

## 5. Use Case Recommendations

### Fast Chat / Enhancement

For prompt rewriting and lightweight conversation. Speed matters more than depth.

| RAM | Model | Notes |
|-----|-------|-------|
| 8 GB | Qwen3 4B Q4_K_M | PromptHub default. Fast, capable. |
| 16 GB | Qwen3 8B Q4_K_M | Noticeably better rewrites. |
| 32 GB+ | Qwen3 14B Q4_K_M | Diminishing returns past this for enhancement. |

### Reasoning / Orchestrator

For chain-of-thought, intent classification, and planning. Thinking mode is important here.

| RAM | Model | Notes |
|-----|-------|-------|
| 8 GB | Qwen3 4B Thinking Q4_K_M | PromptHub default orchestrator. |
| 16 GB | Phi-4 14B Q4_K_M | Strong reasoning per parameter. |
| 32 GB+ | Qwen3 14B Q4_K_M | Good balance. DeepSeek R1 14B distill is an alternative for deeper reasoning. |

### Coding

For code generation, completion, and refactoring in IDE copilots or Claude Code.

| RAM | Model | Notes |
|-----|-------|-------|
| 8 GB | Qwen3 4B Q4_K_M | Handles simple completions. |
| 16 GB | Devstral Small 24B Q3_K_M | Code-specialized. Tight fit at Q3 but very capable. |
| 32 GB+ | Devstral Small 24B Q5_K_M | Higher quality quant. Qwen3 Coder 30B (MoE, A3B active) is also excellent. |

### Assistant

For general-purpose use in Open WebUI, Claude Desktop passthrough, or direct chat.

| RAM | Model | Notes |
|-----|-------|-------|
| 8 GB | Gemma 3 4B Q4_K_M | Vision support at a small size. |
| 16 GB | Qwen3 8B Q4_K_M | Strong all-rounder. |
| 32 GB | Qwen3 14B Q4_K_M | Excellent instruction following. |
| 64 GB+ | Llama 3.3 70B Q4_K_M | Near cloud-quality for general tasks. |

### Agent / Tool Calling

For MCP tool orchestration and multi-step agentic workflows. The model must support structured tool calling.

| RAM | Model | Notes |
|-----|-------|-------|
| 8 GB | Qwen3 4B Q4_K_M | Trained for tool use. Handles simple tool chains. |
| 16 GB | Qwen3 8B Q4_K_M | More reliable multi-step tool use. GPT-OSS 20B Q3 is an alternative. |
| 32 GB+ | Qwen3 14B Q4_K_M | Reliable complex tool chains. GPT-OSS 20B Q4 also strong. |

> In LM Studio, verify the model card shows tool calling support. Not all quantizations preserve tool-use fine-tuning.

### Inline / Completions

For tab-complete and fill-in-the-middle (FIM) in editors. Latency is critical -- smaller models win here.

| RAM | Model | Notes |
|-----|-------|-------|
| 8 GB | Phi-4 Mini 3.8B Q4_K_M | Fast, good completion quality. Qwen3 4B Q4 also works. |
| 16 GB | Qwen3 4B Q6_K | Same model, higher quality quant. Speed stays excellent. |
| 32 GB+ | Qwen3 4B Q8_0 | Near-original quality. No reason to go bigger for inline. |

> For inline completions, do not use models larger than 8B. The latency cost outweighs any quality gain.

### Research

For summarization and search augmentation in tools like Perplexity or Raycast.

| RAM | Model | Notes |
|-----|-------|-------|
| 8 GB | Qwen3 4B Q4_K_M | Adequate for summarization. |
| 16 GB | Qwen3 8B Q4_K_M | Better extraction and synthesis. |
| 32 GB+ | Qwen3 14B Q4_K_M | Strong long-document summarization. |

### Embedding

For vector search, RAG, and semantic similarity. Always use full precision or near-full precision -- quantization hurts embedding quality disproportionately.

| Model | Size | Notes |
|-------|------|-------|
| Nomic Embed Text v1.5 | 84 MB (Q4_K_M) | Lightweight, battle-tested. Good default. |
| Qwen3 Embedding 0.6B | 639 MB (F16) | Better multilingual coverage. Use F16 for embeddings. |

> Embedding models are small enough that full precision is practical. Do not quantize below Q6 for embedding tasks.

---

## 6. PromptHub's Current Setup

This is what PromptHub runs by default and why.

```
LLM:        qwen/qwen3-4b-2507          (Fast Chat — enhancement for all clients)
LLM:        qwen/qwen3-4b-thinking-2507 (Reasoning — orchestrator intent classification)
Embedding:  text-embedding-nomic-embed-text-v1.5 (standby — future RAG pipeline)

Total:      ~5.1 GB loaded, 5.72 GB on disk
Hardware:   Apple Silicon, 16+ GB unified memory
Engine:     mlx-llm v1.4.0 (LLMs), llama.cpp v2.8.0 (embeddings)
```

**Why these models?**

- **Qwen3 4B** is fast enough for real-time prompt enhancement (~20-40 tokens/sec on MLX) without noticeable delay. PromptHub enhances every prompt before forwarding it, so latency matters more than peak quality.
- **Qwen3 4B Thinking** adds chain-of-thought for the orchestrator's intent classification without requiring a larger model. The thinking mode activates only when the model needs to reason about ambiguous prompts.
- **Both models stay loaded simultaneously** to avoid model-swap latency. At ~2.5 GB each, they fit comfortably in 16 GB with room for macOS and apps.

> PromptHub works with any OpenAI-compatible server. These recommendations assume [LM Studio](https://lmstudio.ai/docs) but also apply to Ollama, llama.cpp server, or vLLM.

---

## 7. Tips

**Start small, scale up.** A fast 4B model beats a slow 14B model for prompt enhancement. Measure your actual latency before upgrading -- you may not need a bigger model.

**Keep both LLMs loaded.** PromptHub uses two models (enhancement + orchestrator). If LM Studio swaps models on each request, you pay a multi-second load penalty every time. Disable "Only Keep Last JIT Loaded Model" in LM Studio settings if using multiple models.

**Use MLX on Apple Silicon.** The MLX engine is consistently faster than llama.cpp for most model sizes on Apple Silicon. Check the engine selector in LM Studio when loading a model.

**Set model TTL appropriately.** For always-on models (enhancement, orchestrator), set TTL to unlimited or a long duration (30+ min). For on-demand models, 5-10 minutes avoids wasting memory while preventing cold starts on repeated use.

**Match quantization to role.** Use Q4_K_M as your default. Go higher (Q5, Q6) for Coding and Reasoning roles where quality matters. Go lower (Q3) only when you need to fit a model that would otherwise not load.

**Watch for MoE gotchas.** MoE models (Qwen3.5 A3B, Llama 4 Scout) need RAM for all parameters even though only a fraction activates per token. Check the full model file size, not just the active parameter count.

**Embedding models are different.** Do not apply the same quantization rules. Embedding quality degrades faster with quantization than generative quality does. Use F16 or Q8 for embedding models.

**Test tool calling explicitly.** Not every model or quantization supports structured tool calling. Before assigning a model to the Agent role, test it with a simple tool-calling prompt in LM Studio's chat to confirm it produces valid JSON tool calls.

---

*For PromptHub configuration details, see the [Client Setup Guide](06-client-configuration-guide.md). For OpenAI-compatible proxy setup, see the [OpenAI API Guide](04-openai-api-guide.md). For LM Studio documentation, visit [lmstudio.ai/docs](https://lmstudio.ai/docs).*
