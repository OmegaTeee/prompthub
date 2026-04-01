---
title: "Model Card: text-embedding-nomic-embed-text-v1.5 — Legacy Embedding Model"
status: active
created: 2026-03-28
updated: 2026-03-28
tags: [embedding, nomic, model-card, rag, lm-studio]
---

# text-embedding-nomic-embed-text-v1.5

Nomic Embed Text v1.5. Lightweight legacy embedding model for semantic similarity and retrieval. GGUF format, runs on llama.cpp engine.

## LM Studio Manifest

```
Engine:           llama.cpp v2.8.0 (Apple Metal)
Architecture:     nomic-bert (encoder-only)
Parameters:       137M
Format:           GGUF
Quantization:     Q4_K_M
Disk Size:        84 MB
Context Window:   2,048 tokens
Publisher:        nomic-ai
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | No | Encoder-only — cannot generate text |
| Tool calling | No | |
| Thinking mode | No | |
| Vision | No | |
| Embeddings | Yes | Dense retrieval, 768 dimensions |

## PromptHub Roles

Not currently wired into PromptHub's pipeline. Available for:
- Future RAG document embedding
- Semantic similarity cache keys
- External tools (Open WebUI RAG, LangChain) via LM Studio's `/v1/embeddings`

## Recommendations

- **Tiny footprint**: 84 MB on disk. Negligible resource impact.
- **Being superseded** by `text-embedding-qwen3-embedding-0.6b` which has better multilingual coverage and larger parameter count.
