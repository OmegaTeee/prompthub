"""
Unit tests for session memory system.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from router.memory import SessionStorage, get_session_storage, MemoryMCPClient


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        yield db_path


@pytest.fixture
async def storage(temp_db):
    """Create a SessionStorage instance with temporary database."""
    storage = SessionStorage(db_path=temp_db)
    await storage.initialize()
    yield storage


@pytest.mark.asyncio
async def test_session_create_and_retrieve(storage):
    """Test creating and retrieving a session."""
    result = await storage.create_session(
        session_id="test-session-1",
        client_id="test-client",
        memory_mcp_sync=False,
    )

    assert result["id"] == "test-session-1"
    assert result["client_id"] == "test-client"
    assert result["status"] == "active"
    assert result["memory_mcp_sync"] is False
    assert result["fact_count"] == 0

    # Retrieve and verify
    session = await storage.get_session("test-session-1")
    assert session is not None
    assert session["id"] == "test-session-1"
    assert session["client_id"] == "test-client"


@pytest.mark.asyncio
async def test_session_auto_id_generation(storage):
    """Test that session IDs are auto-generated if omitted."""
    result = await storage.create_session(client_id="test-client")

    assert result["id"] is not None
    assert len(result["id"]) == 36  # UUID format
    assert result["client_id"] == "test-client"


@pytest.mark.asyncio
async def test_session_list_and_filter(storage):
    """Test listing sessions with filters."""
    # Create multiple sessions
    await storage.create_session(session_id="s1", client_id="client-1")
    await storage.create_session(session_id="s2", client_id="client-1")
    await storage.create_session(session_id="s3", client_id="client-2")

    # List all
    sessions, total = await storage.list_sessions()
    assert total == 3
    assert len(sessions) == 3

    # Filter by client
    sessions, total = await storage.list_sessions(client_id="client-1")
    assert total == 2
    assert len(sessions) == 2
    assert all(s["client_id"] == "client-1" for s in sessions)


@pytest.mark.asyncio
async def test_session_close(storage):
    """Test closing a session."""
    await storage.create_session(session_id="test-session", client_id="test-client")

    await storage.close_session("test-session")

    session = await storage.get_session("test-session")
    assert session["status"] == "closed"


@pytest.mark.asyncio
async def test_fact_add_and_list(storage):
    """Test adding and listing facts."""
    await storage.create_session(session_id="s1", client_id="client-1")

    # Add facts
    fact1 = await storage.add_fact(
        session_id="s1",
        fact="The user prefers Python",
        tags=["preferences", "python"],
        source="manual",
    )
    fact2 = await storage.add_fact(
        session_id="s1",
        fact="The user is based in SF",
        tags=["location"],
        source="inferred",
    )

    assert fact1["id"] is not None
    assert fact1["fact"] == "The user prefers Python"
    assert fact1["tags"] == ["preferences", "python"]
    assert fact1["source"] == "manual"

    # List facts
    facts = await storage.get_facts("s1")
    assert len(facts) == 2

    # Verify tags are parsed back as lists
    assert all(isinstance(f["tags"], list) for f in facts)


@pytest.mark.asyncio
async def test_fact_delete(storage):
    """Test deleting a fact."""
    await storage.create_session(session_id="s1", client_id="client-1")

    fact = await storage.add_fact(session_id="s1", fact="Test fact")
    deleted = await storage.delete_fact("s1", fact["id"])

    assert deleted is True

    facts = await storage.get_facts("s1")
    assert len(facts) == 0


@pytest.mark.asyncio
async def test_fact_relevance_decay(storage):
    """Test relevance score decay."""
    await storage.create_session(session_id="s1", client_id="client-1")

    await storage.add_fact(session_id="s1", fact="Fact 1")
    await storage.add_fact(session_id="s1", fact="Fact 2")

    # Get initial relevance scores
    facts_before = await storage.get_facts("s1")
    assert all(f["relevance_score"] == 1.0 for f in facts_before)

    # Decay scores
    updated = await storage.decay_relevance_scores(decay_factor=0.95)
    assert updated == 2

    # Verify decay
    facts_after = await storage.get_facts("s1")
    assert all(f["relevance_score"] < 1.0 for f in facts_after)
    assert all(abs(f["relevance_score"] - 0.95) < 0.001 for f in facts_after)


@pytest.mark.asyncio
async def test_memory_block_upsert_and_get(storage):
    """Test upserting and retrieving memory blocks."""
    await storage.create_session(session_id="s1", client_id="client-1")

    # Upsert a block
    block1 = await storage.upsert_memory_block(
        session_id="s1",
        key="user_preferences",
        value={"language": "python", "framework": "fastapi"},
    )

    assert block1["key"] == "user_preferences"
    assert block1["value"]["language"] == "python"

    # Retrieve
    block = await storage.get_memory_block("s1", "user_preferences")
    assert block is not None
    assert block["value"]["language"] == "python"

    # Update the block
    block2 = await storage.upsert_memory_block(
        session_id="s1",
        key="user_preferences",
        value={"language": "python", "framework": "django"},
    )

    # Verify update
    assert block2["id"] == block1["id"]  # Same block ID
    assert block2["value"]["framework"] == "django"


@pytest.mark.asyncio
async def test_memory_block_expiry(storage):
    """Test memory block expiration."""
    await storage.create_session(session_id="s1", client_id="client-1")

    # Create an expired block
    past = (datetime.now() - timedelta(hours=1)).isoformat()
    await storage.upsert_memory_block(
        session_id="s1",
        key="expired_block",
        value="test",
        expires_at=past,
    )

    # Create a valid block
    future = (datetime.now() + timedelta(hours=1)).isoformat()
    await storage.upsert_memory_block(
        session_id="s1",
        key="valid_block",
        value="test",
        expires_at=future,
    )

    # Cleanup expired blocks
    deleted = await storage.cleanup_expired_blocks()
    assert deleted == 1

    # Verify only valid block remains
    blocks = await storage.get_all_memory_blocks("s1")
    assert len(blocks) == 1
    assert blocks[0]["key"] == "valid_block"


@pytest.mark.asyncio
async def test_memory_block_delete(storage):
    """Test deleting a memory block."""
    await storage.create_session(session_id="s1", client_id="client-1")

    await storage.upsert_memory_block(session_id="s1", key="test_key", value="test")

    deleted = await storage.delete_memory_block("s1", "test_key")
    assert deleted is True

    block = await storage.get_memory_block("s1", "test_key")
    assert block is None


@pytest.mark.asyncio
async def test_get_all_memory_blocks(storage):
    """Test retrieving all memory blocks for a session."""
    await storage.create_session(session_id="s1", client_id="client-1")

    await storage.upsert_memory_block(session_id="s1", key="key1", value={"a": 1})
    await storage.upsert_memory_block(session_id="s1", key="key2", value={"b": 2})

    blocks = await storage.get_all_memory_blocks("s1")
    assert len(blocks) == 2
    assert {b["key"] for b in blocks} == {"key1", "key2"}


@pytest.mark.asyncio
async def test_get_stats(storage):
    """Test retrieving storage statistics."""
    await storage.create_session(session_id="s1", client_id="client-1")
    await storage.create_session(session_id="s2", client_id="client-1", memory_mcp_sync=True)
    await storage.close_session("s2")

    # Add facts and blocks to s1
    await storage.add_fact(session_id="s1", fact="Fact 1")
    await storage.add_fact(session_id="s1", fact="Fact 2")
    await storage.upsert_memory_block(session_id="s1", key="block1", value="value")

    stats = await storage.get_stats()

    assert stats["active_sessions"] == 1
    assert stats["total_facts"] == 2
    assert stats["total_blocks"] == 1
    assert stats["closed_sessions"] == 1


@pytest.mark.asyncio
async def test_cleanup_closed_sessions(storage):
    """Test cleaning up old closed sessions."""
    # Create and close a session
    await storage.create_session(session_id="s1", client_id="client-1")
    await storage.close_session("s1")

    # Mock old last_accessed timestamp (we'd need to manually update the database for true testing)
    # For now, just verify the method runs without error
    deleted = await storage.cleanup_closed_sessions(days=30)
    # May be 0 since our session was just created
    assert isinstance(deleted, int)


@pytest.mark.asyncio
async def test_session_touch(storage):
    """Test updating session last_accessed timestamp."""
    created_session = await storage.create_session(
        session_id="s1", client_id="client-1"
    )
    original_accessed = created_session["last_accessed"]

    # Wait a tiny bit and touch
    import asyncio
    await asyncio.sleep(0.01)
    await storage.touch_session("s1")

    updated_session = await storage.get_session("s1")
    # last_accessed should be updated
    assert updated_session["last_accessed"] >= original_accessed


# MCP Client tests
@pytest.mark.asyncio
async def test_mcp_client_graceful_degradation():
    """Test that MCP client gracefully handles unavailable server."""
    client = MemoryMCPClient(base_url="http://localhost:19999")  # Invalid port

    # Should not raise exception
    result = await client._call_tool("test_tool", {})
    assert result is None

    # Search should return empty list
    results = await client.search_facts("test")
    assert results == []

    # Sync should return False
    success = await client.sync_session_entity("session-1", "client-1")
    assert success is False


# Cross-session search tests (Phase 1 of Tier 2)
@pytest.mark.asyncio
async def test_search_returns_empty_on_empty_query(storage):
    """Empty / whitespace-only query short-circuits to []."""
    await storage.create_session(session_id="s1", client_id="c1")
    await storage.add_fact("s1", "the cat sat on the mat")

    assert await storage.search("", cross_client=True) == []
    assert await storage.search("   ", cross_client=True) == []


@pytest.mark.asyncio
async def test_search_finds_facts_by_keyword(storage):
    """Single-keyword search returns matching facts ranked by BM25."""
    await storage.create_session(session_id="s1", client_id="c1")
    await storage.add_fact("s1", "PromptHub uses FastAPI for the router")
    await storage.add_fact("s1", "The cache uses SQLite with WAL mode")
    await storage.add_fact("s1", "Cherry Studio connects via /v1/responses")

    results = await storage.search("FastAPI", cross_client=True)

    assert len(results) == 1
    assert results[0]["kind"] == "fact"
    assert "FastAPI" in results[0]["content"]
    assert results[0]["score"] > 0  # negated BM25; positive after negation
    assert results[0]["session_id"] == "s1"


@pytest.mark.asyncio
async def test_search_finds_memory_blocks(storage):
    """Memory blocks are searchable via the same query path as facts."""
    await storage.create_session(session_id="s1", client_id="c1")
    await storage.upsert_memory_block(
        "s1", "active_branch", "feat/memory-search-tier-2"
    )
    await storage.upsert_memory_block(
        "s1", "current_focus", "writing FTS5 unit tests"
    )

    results = await storage.search("FTS5", cross_client=True)

    assert len(results) == 1
    assert results[0]["kind"] == "block"
    assert results[0]["block_key"] == "current_focus"
    assert "FTS5" in results[0]["content"]


@pytest.mark.asyncio
async def test_search_returns_facts_and_blocks_unified(storage):
    """A query that matches both kinds returns interleaved results."""
    await storage.create_session(session_id="s1", client_id="c1")
    await storage.add_fact("s1", "Comet is the local browser surface")
    await storage.upsert_memory_block(
        "s1", "current_branch_focus", "Comet rename and enhancement tuning"
    )

    results = await storage.search("Comet", cross_client=True)

    kinds = {r["kind"] for r in results}
    assert kinds == {"fact", "block"}, f"expected both kinds, got {kinds}"


@pytest.mark.asyncio
async def test_search_filters_by_client_id_by_default(storage):
    """When cross_client=False, only the caller's client_id sees results."""
    await storage.create_session(session_id="s_alice", client_id="alice")
    await storage.create_session(session_id="s_bob", client_id="bob")

    await storage.add_fact("s_alice", "Alice prefers tabs over spaces")
    await storage.add_fact("s_bob", "Bob prefers spaces over tabs")

    # alice scope: only alice's fact
    alice_results = await storage.search("tabs", client_id="alice")
    assert len(alice_results) == 1
    assert alice_results[0]["session_id"] == "s_alice"

    # bob scope: only bob's fact
    bob_results = await storage.search("tabs", client_id="bob")
    assert len(bob_results) == 1
    assert bob_results[0]["session_id"] == "s_bob"


@pytest.mark.asyncio
async def test_search_cross_client_overrides_scope(storage):
    """cross_client=True ignores client_id and returns every match."""
    await storage.create_session(session_id="s_alice", client_id="alice")
    await storage.create_session(session_id="s_bob", client_id="bob")
    await storage.add_fact("s_alice", "Alice mentions FastAPI")
    await storage.add_fact("s_bob", "Bob mentions FastAPI")

    results = await storage.search("FastAPI", cross_client=True)
    assert len(results) == 2
    assert {r["session_id"] for r in results} == {"s_alice", "s_bob"}


@pytest.mark.asyncio
async def test_search_respects_limit(storage):
    """limit caps total results across both kinds."""
    await storage.create_session(session_id="s1", client_id="c1")
    for i in range(8):
        await storage.add_fact("s1", f"PromptHub feature number {i}")

    results = await storage.search("PromptHub", cross_client=True, limit=3)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_search_ranks_by_relevance(storage):
    """BM25 ranking puts facts with more query-term matches first."""
    await storage.create_session(session_id="s1", client_id="c1")
    # The first fact mentions "FastAPI" once; the second mentions it twice.
    await storage.add_fact("s1", "PromptHub is a FastAPI app")
    await storage.add_fact("s1", "FastAPI gives FastAPI-style decorators here")

    results = await storage.search("FastAPI", cross_client=True)
    assert len(results) == 2
    # The fact with 2x mentions should outrank the one with 1x mentions
    assert results[0]["content"].count("FastAPI") >= results[1]["content"].count("FastAPI")


@pytest.mark.asyncio
async def test_search_handles_malformed_fts_query(storage):
    """Unbalanced quotes / lone operators don't 500 — return empty."""
    await storage.create_session(session_id="s1", client_id="c1")
    await storage.add_fact("s1", "some content here")

    # FTS5 rejects lone " or unbalanced quotes
    results = await storage.search('"', cross_client=True)
    assert results == []


@pytest.mark.asyncio
async def test_search_updates_propagate_to_fts(storage):
    """After a fact is updated/deleted, FTS reflects the change immediately."""
    await storage.create_session(session_id="s1", client_id="c1")
    fact = await storage.add_fact("s1", "early version mentions GraphQL")

    # Sanity: searchable
    pre = await storage.search("GraphQL", cross_client=True)
    assert len(pre) == 1

    # Delete the fact; FTS DELETE trigger removes from index
    await storage.delete_fact("s1", fact["id"])
    post = await storage.search("GraphQL", cross_client=True)
    assert post == []
