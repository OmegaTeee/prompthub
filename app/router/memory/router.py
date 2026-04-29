"""
Memory router with REST API endpoints.

Provides session, fact, and memory block endpoints under /sessions prefix.
"""

import logging
from collections.abc import Callable

from fastapi import APIRouter, HTTPException

from router.enhancement import EnhancementService

from .mcp_client import MemoryMCPClient
from .models import (
    FactCreate,
    FactResponse,
    MemoryBlockResponse,
    MemoryBlockUpsert,
    SessionContextResponse,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
)
from .storage import SessionStorage

logger = logging.getLogger(__name__)


def create_memory_router(
    get_storage: Callable[[], SessionStorage],
    get_mcp_client: Callable[[], MemoryMCPClient],
    get_enhancement_service: Callable[[], EnhancementService | None] | None = None,
) -> APIRouter:
    """
    Factory function to create memory router.

    Args:
        get_storage: Callable that returns SessionStorage instance
        get_mcp_client: Callable that returns MemoryMCPClient instance
        get_enhancement_service: Optional callable for LLM server enhancement

    Returns:
        APIRouter configured with /sessions endpoints
    """
    router = APIRouter(prefix="/sessions", tags=["sessions"])

    # POST /sessions — Create session
    @router.post("", response_model=SessionResponse)
    async def create_session(req: SessionCreate) -> SessionResponse:
        """Create a new session."""
        storage = get_storage()
        result = await storage.create_session(
            session_id=req.session_id,
            client_id=req.client_id,
            memory_mcp_sync=req.memory_mcp_sync,
        )

        # Sync to Memory MCP if enabled
        if req.memory_mcp_sync:
            mcp_client = get_mcp_client()
            await mcp_client.sync_session_entity(result["id"], result["client_id"])

        return SessionResponse(**result)

    # GET /sessions — List sessions
    @router.get("", response_model=SessionListResponse)
    async def list_sessions(
        client_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """List sessions with optional filters."""
        storage = get_storage()
        sessions, total = await storage.list_sessions(
            client_id=client_id, status=status, limit=limit, offset=offset
        )

        return SessionListResponse(
            sessions=[SessionResponse(**s) for s in sessions],
            total=total,
            limit=limit,
            offset=offset,
        )

    # GET /sessions/{id} — Get session details
    @router.get("/{session_id}", response_model=SessionResponse)
    async def get_session(session_id: str) -> SessionResponse:
        """Get session details including fact count."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await storage.touch_session(session_id)  # Update last_accessed

        return SessionResponse(**session)

    # DELETE /sessions/{id} — Close session
    @router.delete("/{session_id}")
    async def close_session(session_id: str) -> dict:
        """Close a session."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await storage.close_session(session_id)
        return {"status": "closed", "session_id": session_id}

    # POST /sessions/{id}/facts — Add fact
    @router.post("/{session_id}/facts", response_model=FactResponse)
    async def add_fact(session_id: str, req: FactCreate) -> FactResponse:
        """Add a fact to a session."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await storage.add_fact(
            session_id=session_id,
            fact=req.fact,
            tags=req.tags,
            source=req.source,
        )

        # Sync to Memory MCP if enabled
        if session.get("memory_mcp_sync"):
            mcp_client = get_mcp_client()
            await mcp_client.add_observation(session_id, req.fact)

        return FactResponse(**result)

    # GET /sessions/{id}/facts — List facts
    @router.get("/{session_id}/facts")
    async def get_facts(
        session_id: str, tags: str | None = None, limit: int = 50
    ) -> list[FactResponse]:
        """Get facts for a session with optional tag filter."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        parsed_tags = tags.split(",") if tags else None
        facts = await storage.get_facts(session_id, tags=parsed_tags, limit=limit)

        return [FactResponse(**f) for f in facts]

    # DELETE /sessions/{id}/facts/{fact_id} — Delete fact
    @router.delete("/{session_id}/facts/{fact_id}")
    async def delete_fact(session_id: str, fact_id: int) -> dict:
        """Delete a fact."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        deleted = await storage.delete_fact(session_id, fact_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Fact not found")

        return {"deleted": True, "fact_id": fact_id}

    # PUT /sessions/{id}/memory/{key} — Upsert memory block
    @router.put("/{session_id}/memory/{key}", response_model=MemoryBlockResponse)
    async def upsert_memory_block(
        session_id: str, key: str, req: MemoryBlockUpsert
    ) -> MemoryBlockResponse:
        """Upsert a memory block."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await storage.upsert_memory_block(
            session_id=session_id,
            key=key,
            value=req.value,
            expires_at=req.expires_at,
        )

        return MemoryBlockResponse(**result)

    # GET /sessions/{id}/memory/{key} — Get memory block
    @router.get("/{session_id}/memory/{key}", response_model=MemoryBlockResponse)
    async def get_memory_block(session_id: str, key: str) -> MemoryBlockResponse:
        """Get a memory block by key."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        block = await storage.get_memory_block(session_id, key)

        if not block:
            raise HTTPException(status_code=404, detail="Memory block not found")

        return MemoryBlockResponse(**block)

    # DELETE /sessions/{id}/memory/{key} — Delete memory block
    @router.delete("/{session_id}/memory/{key}")
    async def delete_memory_block(session_id: str, key: str) -> dict:
        """Delete a memory block."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        deleted = await storage.delete_memory_block(session_id, key)

        if not deleted:
            raise HTTPException(status_code=404, detail="Memory block not found")

        return {"deleted": True, "key": key}

    # GET /sessions/{id}/context — Full context (session + facts + blocks + MCP)
    @router.get("/{session_id}/context", response_model=SessionContextResponse)
    async def get_session_context(session_id: str) -> SessionContextResponse:
        """Get complete session context including facts, blocks, and MCP graph."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await storage.touch_session(session_id)

        # Get facts (most relevant first)
        facts = await storage.get_facts(session_id, limit=50)

        # Get memory blocks
        blocks = await storage.get_all_memory_blocks(session_id)

        # Try to get MCP graph if sync enabled
        mcp_graph_summary = None
        if session.get("memory_mcp_sync"):
            mcp_client = get_mcp_client()
            graph = await mcp_client.get_session_graph(session_id)
            if graph:
                # Summarize graph (e.g., node count, edge count)
                mcp_graph_summary = f"Graph with {len(graph.get('nodes', []))} nodes"

        return SessionContextResponse(
            session=SessionResponse(**session),
            facts=[FactResponse(**f) for f in facts],
            memory_blocks=[MemoryBlockResponse(**b) for b in blocks],
            mcp_graph_summary=mcp_graph_summary,
        )

    # POST /sessions/{id}/summarize — Generate context summary via LLM server
    @router.post("/{session_id}/summarize")
    async def summarize_session(session_id: str) -> dict:
        """Generate a context summary via LLM server."""
        storage = get_storage()
        session = await storage.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get facts for summarization
        facts = await storage.get_facts(session_id, limit=20)

        if not facts:
            summary = "No facts to summarize"
        elif not get_enhancement_service:
            summary = f"Skipped (enhancement service not available): {len(facts)} facts"
        else:
            # Use enhancement service to summarize
            enhancement = get_enhancement_service()
            if not enhancement:
                summary = f"Enhancement service unavailable: {len(facts)} facts"
            else:
                fact_text = "\n".join([f["fact"] for f in facts])
                prompt = f"Summarize the following facts concisely:\n\n{fact_text}"

                try:
                    summary = await enhancement.enhance(
                        prompt,
                        client_name="system",
                        system_prompt="You are a summarization assistant. Keep summaries under 200 words.",
                    )
                except Exception as e:
                    logger.warning(f"Summary generation failed: {e}")
                    summary = f"Summary generation failed: {e}"

        # Store summary
        await storage.get_session(session_id)  # Refresh
        # Note: In a full implementation, we'd update the session's context_summary field
        # For now, just return the summary

        return {"session_id": session_id, "summary": summary}

    return router
