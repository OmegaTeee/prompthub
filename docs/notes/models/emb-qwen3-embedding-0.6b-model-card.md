---
title: "Model Card: text-embedding-qwen3-embedding-0.6b — Primary Embedding Model"
status: active
created: 2026-03-28
updated: 2026-03-28
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

- **Currently loaded** in LM Studio. Ready for use via `/v1/embeddings`.
- **Preferred over Nomic Embed** for new integrations — larger model, same Qwen3 family as the LLMs.
- **639 MB** on disk — moderate footprint but much better embedding quality than the 84 MB Nomic model.
