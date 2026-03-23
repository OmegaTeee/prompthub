---
title: "Model Card: bge-m3 — Embedding Model"
status: final
created: 2026-03-23
updated: 2026-03-23
tags: [llm, bge-m3, model-card, embeddings, rag]
---

# bge-m3

BAAI General Embedding (BGE) M3 model. A multilingual, multi-granularity embedding model for semantic similarity and retrieval. Not a generative model — produces vector representations of text.

## Ollama Manifest

```
Architecture:     bert (encoder-only)
Parameters:       566.7M
Quantization:     F16 (full precision — no quantization loss)
Disk Size:        1.2 GB
Context Window:   8,192 tokens
Embedding Length:  1,024 dimensions
Digest:           790764642607
License:          MIT
```

## Capabilities

| Capability | Supported | Notes |
|---|---|---|
| Completion | No | Encoder-only — cannot generate text |
| Tool calling | No | |
| Thinking mode | No | |
| Vision | No | |
| Embeddings | Yes | Dense, sparse, and multi-vector retrieval |

## Embedding Properties

| Property | Value |
|---|---|
| Dimensions | 1,024 |
| Precision | F16 (no quantization — embedding quality matters) |
| Max input | 8,192 tokens |
| Multilingual | 100+ languages |
| Retrieval modes | Dense, sparse (lexical), multi-vector (ColBERT-style) |

## PromptHub Roles

### 1. Future RAG Pipeline

**Planned in**: [plan-rag-improvement.md](plan-rag-improvement.md) — Phase 2 (PGVector + Document Ingestion)

Not yet wired into PromptHub's request pipeline. Will be used for:
- **Document embedding**: Convert ingested documents into vectors for PGVector storage
- **Semantic search**: Find relevant chunks when enhancing prompts (Phase 3)
- **Prompt similarity**: Cache key generation based on semantic similarity rather than exact hash

### 2. Potential Routing Classifier

Could embed incoming prompts and map them to model lanes based on task-type clusters (vision, code, tool-use, chat). Currently the orchestrator (`qwen3:14b`) handles this with LLM inference, but embedding-based routing would be faster (~10ms vs ~1s).

## Recommendations

- **Tiny footprint**: At 1.2 GB with F16 precision, this model can coexist with any other model in the stack. It adds negligible VRAM pressure.
- **F16 is intentional**: Embedding models should not be quantized — the vector quality directly affects retrieval accuracy. Keep at F16.
- **Not used yet**: This model is installed in preparation for the RAG improvement plan. No PromptHub code currently calls it.
- **Alternative use**: Ollama exposes `bge-m3` at `POST /api/embed`. External tools (Open WebUI RAG, LangChain) can use it directly without going through PromptHub.
