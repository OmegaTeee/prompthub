---
title: "Model Card: text-embedding-qwen3-embedding-0.6b — Primary Embedding Model"
status: archived
created: 2026-03-28
updated: 2026-04-05
tags: [embedding, qwen3, model-card, rag, lm-studio]
---

# text-embedding-qwen3-embedding-0.6b

Qwen3 Embedding 0.6B. Primary embedding model — larger and more capable than Nomic Embed. Part of the Qwen3 family, matching the LLM models in the stack.

## LM Studio Manifest

```
Engine:           llama.cpp v2.8.0 (Apple Metal)
Architecture:     qwen3
Parameters:       0.6B
Format:           GGUF
Disk Size:        639 MB
Publisher:        qwen
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | No | Embedding model only |
| Tool calling | No | |
| Thinking mode | No | |
| Vision | No | |
| Embeddings | Yes | Dense retrieval |

## PromptHub Roles

Not currently wired into PromptHub's pipeline. Available for:
- Future RAG document embedding (preferred over Nomic Embed for quality)
- Semantic similarity for prompt caching
- External tools via LM Studio's `/v1/embeddings`

## Recommendations

- **Removed from LM Studio** (2026-04-05). Nomic Embed Text v1.5 is now the sole embedding model.
- **639 MB** on disk — was a capable embedding model but not needed given current usage patterns.
