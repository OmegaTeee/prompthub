"""
Unit tests for router.tool_registry.storage

Tests cover:
- cache_tools / get_cached_tools (write + read round-trip)
- Cache expiry (expired entries return None)
- Serve count tracking (incremented on each cache hit)
- invalidate / invalidate_all (archive + delete)
- archive_expired (move expired to archive table)
- cleanup_archive (retention period enforcement)
- get_all_cached (summary listing)
- get_stats (aggregate statistics)
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio

from router.tool_registry.storage import ToolRegistryStorage

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_TOOLS = [
    {
        "name": "search",
        "description": "Search the web",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "fetch",
        "description": "Fetch a URL",
        "inputSchema": {
            "type": "object",
            "properties": {"url": {"type": "string", "format": "uri"}},
            "required": ["url"],
        },
    },
]

SAMPLE_TOOLS_B = [
    {
        "name": "read_file",
        "description": "Read file contents",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]


@pytest_asyncio.fixture
async def storage(tmp_path: Path):
    """Create a fresh ToolRegistryStorage with a temp database."""
    db_path = tmp_path / "test_tool_registry.db"
    s = ToolRegistryStorage(db_path=db_path)
    await s.initialize()
    return s


# ---------------------------------------------------------------------------
# Cache round-trip
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_and_retrieve(storage: ToolRegistryStorage):
    """Cached tools should be retrievable."""
    await storage.cache_tools("duckduckgo", SAMPLE_TOOLS)

    tools = await storage.get_cached_tools("duckduckgo")
    assert tools is not None
    assert len(tools) == 2
    assert tools[0]["name"] == "search"
    assert tools[1]["name"] == "fetch"


@pytest.mark.asyncio
async def test_cache_miss_returns_none(storage: ToolRegistryStorage):
    """Unknown server should return None."""
    result = await storage.get_cached_tools("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_cache_upsert_archives_previous(storage: ToolRegistryStorage):
    """Re-caching a server should archive the previous snapshot."""
    await storage.cache_tools("server-a", SAMPLE_TOOLS)
    await storage.cache_tools("server-a", SAMPLE_TOOLS_B)

    # Current cache should have the new tools
    tools = await storage.get_cached_tools("server-a")
    assert tools is not None
    assert len(tools) == 1
    assert tools[0]["name"] == "read_file"

    # Archive should have the old snapshot
    stats = await storage.get_stats()
    assert stats["archived_snapshots"] >= 1


# ---------------------------------------------------------------------------
# Expiry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_cache_returns_none(storage: ToolRegistryStorage):
    """Expired cache entries should return None."""
    await storage.cache_tools("expiring", SAMPLE_TOOLS, ttl_hours=0)

    # Force expiry by setting expires_at in the past
    import aiosqlite

    past = (datetime.now() - timedelta(hours=1)).isoformat()
    async with aiosqlite.connect(str(storage.db_path)) as db:
        await db.execute(
            "UPDATE tool_cache SET expires_at = ? WHERE server_name = ?",
            (past, "expiring"),
        )
        await db.commit()

    result = await storage.get_cached_tools("expiring")
    assert result is None


# ---------------------------------------------------------------------------
# Serve count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_serve_count_increments(storage: ToolRegistryStorage):
    """Each cache hit should increment serve_count."""
    await storage.cache_tools("counter", SAMPLE_TOOLS)

    # Hit cache 3 times
    for _ in range(3):
        await storage.get_cached_tools("counter")

    snapshots = await storage.get_all_cached()
    counter = next(s for s in snapshots if s["server_name"] == "counter")
    assert counter["serve_count"] == 3


# ---------------------------------------------------------------------------
# Invalidation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_archives_and_deletes(storage: ToolRegistryStorage):
    """Invalidation should archive then delete the cache entry."""
    await storage.cache_tools("doomed", SAMPLE_TOOLS)

    deleted = await storage.invalidate("doomed")
    assert deleted is True

    # Cache miss
    assert await storage.get_cached_tools("doomed") is None

    # Archived
    stats = await storage.get_stats()
    assert stats["archived_snapshots"] >= 1


@pytest.mark.asyncio
async def test_invalidate_nonexistent_returns_false(
    storage: ToolRegistryStorage,
):
    """Invalidating a non-cached server should return False."""
    result = await storage.invalidate("ghost")
    assert result is False


@pytest.mark.asyncio
async def test_invalidate_all(storage: ToolRegistryStorage):
    """invalidate_all should clear everything and archive."""
    await storage.cache_tools("a", SAMPLE_TOOLS)
    await storage.cache_tools("b", SAMPLE_TOOLS_B)

    count = await storage.invalidate_all()
    assert count == 2

    snapshots = await storage.get_all_cached()
    assert len(snapshots) == 0

    stats = await storage.get_stats()
    assert stats["archived_snapshots"] >= 2


# ---------------------------------------------------------------------------
# Archive operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_archive_expired(storage: ToolRegistryStorage):
    """archive_expired should move expired entries to archive."""
    await storage.cache_tools("fresh", SAMPLE_TOOLS, ttl_hours=24)
    await storage.cache_tools("stale", SAMPLE_TOOLS_B, ttl_hours=0)

    # Force stale to be expired
    import aiosqlite

    past = (datetime.now() - timedelta(hours=1)).isoformat()
    async with aiosqlite.connect(str(storage.db_path)) as db:
        await db.execute(
            "UPDATE tool_cache SET expires_at = ? WHERE server_name = ?",
            (past, "stale"),
        )
        await db.commit()

    count = await storage.archive_expired()
    assert count == 1

    # fresh should still be cached
    assert await storage.get_cached_tools("fresh") is not None
    # stale should be gone
    assert await storage.get_cached_tools("stale") is None


@pytest.mark.asyncio
async def test_cleanup_archive(storage: ToolRegistryStorage):
    """cleanup_archive should delete old archived snapshots."""
    # Create and invalidate to generate archive entries
    await storage.cache_tools("old", SAMPLE_TOOLS)
    await storage.invalidate("old")

    # Force archived_at to be old
    import aiosqlite

    old_date = (datetime.now() - timedelta(days=100)).isoformat()
    async with aiosqlite.connect(str(storage.db_path)) as db:
        await db.execute(
            "UPDATE tool_cache_archive SET archived_at = ?", (old_date,)
        )
        await db.commit()

    count = await storage.cleanup_archive(retention_days=90)
    assert count >= 1

    stats = await storage.get_stats()
    assert stats["archived_snapshots"] == 0


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stats(storage: ToolRegistryStorage):
    """Stats should reflect current state accurately."""
    await storage.cache_tools("s1", SAMPLE_TOOLS)
    await storage.cache_tools("s2", SAMPLE_TOOLS_B)

    stats = await storage.get_stats()
    assert stats["cached_servers"] == 2
    assert stats["total_tools"] == 3  # 2 + 1
    assert stats["total_size_bytes"] > 0
    assert stats["oldest_snapshot"] is not None
    assert stats["newest_snapshot"] is not None


@pytest.mark.asyncio
async def test_get_all_cached(storage: ToolRegistryStorage):
    """get_all_cached should list all servers without tool definitions."""
    await storage.cache_tools("alpha", SAMPLE_TOOLS)
    await storage.cache_tools("beta", SAMPLE_TOOLS_B)

    snapshots = await storage.get_all_cached()
    assert len(snapshots) == 2
    names = {s["server_name"] for s in snapshots}
    assert names == {"alpha", "beta"}

    # Should not include tools_json (summary only)
    for s in snapshots:
        assert "tools_json" not in s


@pytest.mark.asyncio
async def test_get_snapshot_full(storage: ToolRegistryStorage):
    """get_snapshot should return full tool definitions."""
    await storage.cache_tools("full", SAMPLE_TOOLS)

    snapshot = await storage.get_snapshot("full")
    assert snapshot is not None
    assert snapshot["server_name"] == "full"
    assert len(snapshot["tools"]) == 2
    assert snapshot["tools"][0]["name"] == "search"


# ---------------------------------------------------------------------------
# Vacuum
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vacuum(storage: ToolRegistryStorage):
    """vacuum should not raise."""
    await storage.cache_tools("v", SAMPLE_TOOLS)
    await storage.invalidate("v")
    await storage.vacuum()  # Should not raise
