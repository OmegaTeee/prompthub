---
title: "PromptHub RAG & Workflow Improvement Plan"
status: draft
created: 2026-03-21
updated: 2026-03-23
tags: [plan, rag, pgvector, langchain, n8n, roadmap]
---

# PromptHub RAG & Workflow Improvement Plan

**Created:** 2026-03-21
**Branch:** `feature/prompthub-rag-improvements`
**Source:** Gap analysis comparing Work Buddy's LangChain RAG pipeline with PromptHub's current capabilities

---

## Executive Summary

PromptHub currently enhances prompts statelessly — each request is processed in isolation with no semantic search, no document grounding, and no learning from past enhancements. Work Buddy demonstrates a complete LangChain RAG pipeline (PGVector, history-aware retrieval, document ingestion) that can be ported to PromptHub to unlock context-aware enhancement, project document search, and automated knowledge pipelines.

**Last audited:** 2026-03-21

---

## Dependency Graph

```
Phase 1 (Session Context) — independent, no new infrastructure
Phase 2 (PGVector + Ingestion) — independent of Phase 1
Phase 3 (RAG Enhancement) — depends on Phase 2 (needs PGVector)
Phase 4 (n8n Integration) — depends on Phase 2 (needs ingestion endpoints)
Phases 3 and 4 are independent of each other and can be parallelized.
```

---

## Rollback Strategy

Each phase should be gated behind a feature flag in `router/config/settings.py`:
- `ENABLE_SESSION_CONTEXT_ENHANCEMENT = False` (Phase 1)
- `ENABLE_RAG_INGESTION = False` (Phase 2)
- `ENABLE_RAG_ENHANCEMENT = False` (Phase 3)
- `ENABLE_WEBHOOK_INGESTION = False` (Phase 4)

If any phase destabilizes the system, set the flag to False to disable without code revert.

---

## Gap Analysis

| Capability | PromptHub (Current) | Work Buddy (Reference) | Gap Impact |
|-----------|---------------------|----------------------|------------|
| Vector embeddings | None — SQLite text-only | PGVector + nomic-embed-text (768 dims) | HIGH |
| Document ingestion | None | 12 file formats via FileLoaderService | HIGH |
| History-aware retrieval | None | LangChain createHistoryAwareRetriever | HIGH |
| RAG chains | None | Full pipeline (retrieve → stuff → stream) | HIGH |
| Session context in enhancement | OrchestratorAgent uses it, but enhancement middleware never passes it | N/A | QUICK WIN |
| Chunking strategy | None | RecursiveCharacterTextSplitter (1000/50) | MEDIUM |

---

## Phase 1: Wire Session Context into Enhancement (Quick Win)

**Goal:** Make enhancement context-aware using existing session facts
**Effort:** 3-5 days (includes signature changes, cache key updates, and tests)
**Files to modify:**
- `router/middleware/enhancement.py` — fetch session facts before calling enhance(). **Note:** currently only processes `/mcp/` paths; decide whether to also apply to `/v1/chat/completions`
- `router/enhancement/service.py` — **add `session_context` parameter** to `enhance()` method (currently not in signature). Update system prompt construction to include context. **Update cache key** to incorporate session context hash (otherwise identical prompts with different session facts return stale cached results)
- `router/orchestrator/agent.py` — already accepts and uses `session_context` in `_build_user_message()` and the `/ollama/orchestrate` endpoint. The gap is that the **enhancement middleware path** never populates it.

**Session ID resolution:** The memory router uses explicit `session_id` path params. Enhancement middleware must resolve session ID from the request — options:
- Derive from `client_name` (one session per client)
- Accept `X-Session-Id` header from clients
- Create a mapping endpoint: `GET /sessions?client_name=raycast`

**Implementation:**
1. Add `session_context: str | None = None` param to `EnhancementService.enhance()`
2. If session_context is provided, append to system prompt before LLM call
3. Update cache key to include `hash(session_context)` to prevent stale results
4. In enhancement middleware, resolve session ID → fetch recent facts → pass as session_context
5. Update all callers of `enhance()` (middleware line 49, `/ollama/enhance` endpoint line 77)
6. Gate behind `ENABLE_SESSION_CONTEXT_ENHANCEMENT` feature flag
7. Add tests for: with context, without context, cache invalidation on context change

**LangChain concept learned:** System prompt augmentation with dynamic context — the same pattern used in RAG chains to inject retrieved documents.

**Acceptance criteria:**
- [ ] `enhance()` accepts optional `session_context` parameter
- [ ] Cache key incorporates session context hash
- [ ] Enhancement middleware fetches session facts (limit 5, ordered by relevance_score)
- [ ] Session ID resolution strategy implemented and documented
- [ ] Enhanced prompts reference session context when relevant
- [ ] No latency regression > 50ms when session has facts
- [ ] Existing enhancement behavior unchanged when no session exists
- [ ] Feature flag disables session context injection when set to False
- [ ] Unit tests cover: with/without context, cache behavior, flag toggling

---

## Phase 2: Add PGVector + Document Ingestion Endpoints

**Goal:** Enable PromptHub to ingest and semantically search project documents
**Effort:** Medium (1-2 weeks)
**New files:**
- `router/rag/__init__.py`
- `router/rag/vector_store.py` — PGVector operations (port from Work Buddy's PGVectorService)
- `router/rag/document_loader.py` — Multi-format loader (port from FileLoaderService)
- `router/rag/chunking.py` — Chunking strategies with adaptive sizing
- `router/rag/router.py` — FastAPI endpoints for ingestion and search

**Dependencies to add:**
```
langchain-community[pgvector]
langchain-ollama
langchain-core
pgvector
asyncpg
```

**Endpoints:**
```
POST /projects/{project_id}/documents    — Upload and embed documents
DELETE /projects/{project_id}/documents   — Remove documents by metadata
GET /projects/{project_id}/documents      — List ingested documents
POST /projects/{project_id}/query         — Semantic similarity search
```

**Docker changes:**
- Add pgvector service to existing docker-compose (or extend Work Buddy's existing `pgvector/pgvector:pg16`)
- Init script: CREATE EXTENSION vector; CREATE TABLE project_documents (...)
- **Note:** This introduces PostgreSQL alongside the existing SQLite (used for session storage and cache). PGVector should have its own connection pool, health check, and failure isolation so SQLite-backed features remain unaffected if PGVector is down.

**Dependency note:** Verify `asyncpg` vs `psycopg` — LangChain's PGVector integration typically uses `psycopg` or `sqlalchemy`. Check the specific `langchain-community[pgvector]` version for its driver requirement.

**Migration strategy:** Use raw SQL migration scripts in a `migrations/` directory (numbered: `001_create_project_documents.sql`, etc.) rather than an ORM. Keep it simple for now; add alembic if schema changes become frequent.

**LangChain concepts learned:**
- `RecursiveCharacterTextSplitter` — how chunking affects retrieval quality
- `OllamaEmbeddings` — converting text to vectors locally
- `PGVector` — similarity search with metadata filtering
- Document loading pipeline — Blob → Loader → Document → Chunks → Embeddings → Store

**Acceptance criteria:**
- [ ] Can upload PDF, DOCX, TXT, MD, CSV, JSON files
- [ ] Documents chunked with configurable strategy (default 1000/50)
- [ ] Embeddings stored in PGVector with project_id metadata
- [ ] Similarity search returns top-k relevant chunks
- [ ] Delete by filename/project works correctly
- [ ] Health check includes PGVector status

---

## Phase 3: RAG-Enhanced Prompt Improvement

**Goal:** Enhancement service learns from past successful enhancements
**Effort:** Medium (2-3 weeks)
**Files to modify:**
- `router/enhancement/service.py` — add RAG retrieval before enhancement
- `router/rag/vector_store.py` — add prompt_variations table/collection

**New data model:**
```sql
CREATE TABLE prompt_variations (
    id bigserial PRIMARY KEY,
    vector vector(768),
    original_prompt text NOT NULL,
    enhanced_prompt text NOT NULL,
    client_name varchar(100),
    quality_score real DEFAULT 0.0,
    context_hints jsonb,
    created_at timestamp DEFAULT now()
);
```

**New endpoint:**
```
POST /enhancements/{id}/rate    — Submit quality feedback (1-5 score)
```

**Enhancement flow (modified):**
```
1. Receive prompt + client_name
2. Check L1/L2 cache (existing)
3. NEW: Retrieve 3 most similar past enhancements from prompt_variations
4. Format as few-shot examples in system prompt
5. Call Ollama with augmented system prompt
6. Store (original, enhanced, client) as new embedding
7. Return enhanced prompt
```

**LangChain concepts learned:**
- Few-shot prompting with semantic retrieval
- Feedback loops and quality scoring
- Vector store as learning memory (not just document search)

**Cost considerations:**
- Each enhancement now triggers an additional embedding call (nomic-embed-text) to store the result. This doubles the Ollama calls per enhancement request.
- Few-shot examples injected into the system prompt must respect the existing `TokenBudget` system (`router/enhancement/context_window.py`). Cap retrieved examples to fit within budget.

**Acceptance criteria:**
- [ ] Past enhancements stored as embeddings after each successful enhance()
- [ ] Similar past enhancements retrieved and used as few-shot examples
- [ ] Few-shot injection respects TokenBudget limits (truncate or reduce k if needed)
- [ ] Quality feedback endpoint updates quality_score
- [ ] Retrieval weighted by quality_score (higher = more likely selected)
- [ ] Enhancement quality measurably improves with more data (manual eval)
- [ ] Feature flag disables RAG enhancement when set to False

---

## Phase 4: n8n Integration & Automated Pipelines

**Goal:** Enable automated knowledge ingestion via n8n workflows
**Effort:** Small-Medium (1-2 weeks)
**Prerequisites:** Phase 2 complete

**n8n workflow examples:**

### Workflow 1: GitHub PR → Auto-Ingest Changed Files
```
Trigger: GitHub webhook (PR opened/updated)
Steps:
  1. Fetch changed files via GitHub API
  2. POST each file to PromptHub /projects/{repo}/documents
  3. Notify via Slack/webhook on completion
```

### Workflow 2: Weekly Knowledge Sync
```
Trigger: Cron (every Monday 9am)
Steps:
  1. Fetch updated pages from Notion/Confluence API
  2. POST to PromptHub /projects/{workspace}/documents
  3. Log sync results to audit endpoint
```

### Workflow 3: Enhancement Quality Review
```
Trigger: Cron (daily)
Steps:
  1. GET /audit/recent?type=enhancement (past 24h)
  2. Sample 5 enhancements
  3. POST to /v1/chat/completions asking LLM to rate quality
  4. POST ratings to /enhancements/{id}/rate
```

**PromptHub changes needed:**
- Webhook endpoint: `POST /webhooks/{project_id}/ingest` (accepts raw file content). **Security:** Requires bearer token auth (reuse api-keys.json) + rate limiting to prevent abuse.
- Bulk ingestion: `POST /projects/{project_id}/documents/bulk` with configurable batch size limit (default 50 files) and async queue for large batches.
- Audit query endpoint: `GET /audit/recent?type=...&since=...`

**n8n concepts learned:**
- Webhook triggers vs cron triggers
- HTTP Request node for API calls
- Data transformation between services
- Error handling and retry logic in workflows

**Acceptance criteria:**
- [ ] Webhook endpoint accepts and queues document ingestion
- [ ] Bulk ingestion handles 10+ files in single request
- [ ] n8n can successfully trigger ingestion via webhook
- [ ] Audit endpoint supports filtering by type and time range

---

## How to Revisit This Plan

### Starting a session
```bash
# 1. Switch to the feature branch
cd ~/.local/share/prompthub
git checkout feature/prompthub-rag-improvements

# 2. Check current progress
cat docs/notes/prompthub-rag-improvement-plan.md

# 3. Tell Claude Code:
# "I'm working on the PromptHub RAG improvement plan.
#  Check the plan doc and memory, then let's pick up where we left off."
```

### Between sessions
- This plan document is the source of truth — update acceptance criteria checkboxes as you go
- Project memory at `~/.claude/projects/-Users-visualval-raycast/memory/project_prompthub_rag_improvements.md` provides context for Claude Code
- Phase 1 and Phase 2 are independent of each other. Phases 3 and 4 both depend on Phase 2 but are independent of each other.

### Testing each phase
- Phase 1: Run existing enhancement tests, verify session context appears in logs
- Phase 2: Upload a test PDF, query it, verify relevant chunks returned
- Phase 3: Run 10+ enhancements, verify later ones reference earlier patterns
- Phase 4: Set up n8n locally (Docker), create webhook workflow, trigger ingestion

---

## Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │              PromptHub                    │
                    │                                          │
  n8n Workflows ──► │  /webhooks/{id}/ingest  (Phase 4)       │
                    │         │                                │
  Raycast/Cursor ──►│  /v1/chat/completions                   │
                    │         │                                │
                    │    ┌────▼─────┐    ┌──────────────┐     │
                    │    │Enhancement│◄──►│ RAG Retrieval │     │
                    │    │ Service   │    │ (Phase 3)    │     │
                    │    └────┬─────┘    └──────┬───────┘     │
                    │         │                 │              │
                    │    ┌────▼─────┐    ┌──────▼───────┐     │
                    │    │ Session  │    │  PGVector     │     │
                    │    │ Context  │    │  (Phase 2)    │     │
                    │    │(Phase 1) │    │              │      │
                    │    └──────────┘    └──────────────┘     │
                    │         │                                │
                    │    ┌────▼─────┐                          │
                    │    │  Ollama  │                          │
                    │    └──────────┘                          │
                    └─────────────────────────────────────────┘
```
