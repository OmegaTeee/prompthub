"""
Pydantic models for session memory requests/responses.
"""

from typing import Any

from pydantic import BaseModel, Field


# Request Models
class SessionCreate(BaseModel):
    """Create a new session."""

    client_id: str
    session_id: str | None = None  # auto-UUID if omitted
    memory_mcp_sync: bool = False


class FactCreate(BaseModel):
    """Add a fact to a session."""

    fact: str
    tags: list[str] = []
    source: str = "manual"


class MemoryBlockUpsert(BaseModel):
    """Upsert a memory block in a session."""

    value: Any  # dict | list | str | int | float | bool
    expires_at: str | None = None  # ISO8601


# Response Models
class SessionResponse(BaseModel):
    """Session details."""

    id: str
    client_id: str
    created_at: str
    last_accessed: str
    status: str
    context_summary: str | None
    memory_mcp_sync: bool
    fact_count: int


class FactResponse(BaseModel):
    """Individual fact."""

    id: int
    session_id: str
    fact: str
    tags: list[str]
    created_at: str
    relevance_score: float
    source: str


class MemoryBlockResponse(BaseModel):
    """Memory block (key-value)."""

    id: int
    session_id: str
    key: str
    value: Any
    expires_at: str | None
    created_at: str
    updated_at: str


class SessionContextResponse(BaseModel):
    """Complete session context (facts + blocks + MCP graph)."""

    session: SessionResponse
    facts: list[FactResponse]  # recent N facts, sorted by relevance
    memory_blocks: list[MemoryBlockResponse]
    mcp_graph_summary: str | None  # from Memory MCP read_graph (if sync enabled)


class SessionListResponse(BaseModel):
    """List of sessions with pagination."""

    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int


# Search models
class SearchRequest(BaseModel):
    """Cross-session search query."""

    query: str
    limit: int = Field(default=10, ge=1, le=100)
    cross_client: bool = False
    # client_id is intentionally not in the request body — it's derived
    # from the audit context (X-Client-ID header, populated by
    # router/middleware/audit_context.py) so callers can't search other
    # tenants' data without explicit cross_client=True.


class SearchResult(BaseModel):
    """A single search match (fact or memory block)."""

    kind: str  # "fact" | "block"
    session_id: str
    content: str
    score: float  # higher = more relevant (FTS5 BM25, negated)
    fact_id: int | None = None
    tags: list[str] | None = None
    block_key: str | None = None


class SearchResponse(BaseModel):
    """Search results, ordered by relevance descending."""

    results: list[SearchResult]
    query: str
    limit: int
