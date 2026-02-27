"""
Tests for persistent cache (L1 memory + L2 SQLite).

Verifies:
- Write-through behavior (set writes to both layers)
- L1 hit / L2 fallback / promotion to L1
- TTL expiration in both layers
- LRU eviction preserves L2
- Cache survives instance restart
- L1 warmup from L2
- Stats tracking (l2_hits, l2_size)
- PersistentEnhancementCache convenience API
"""

import pytest
from pathlib import Path

from router.cache.persistent import PersistentCache
from router.cache.persistent_enhancement import PersistentEnhancementCache


@pytest.fixture
def db_path(tmp_path):
    """Isolated database path per test."""
    return tmp_path / "test_cache.db"


class TestPersistentCache:
    """Tests for PersistentCache (L1+L2 hybrid)."""

    @pytest.mark.asyncio
    async def test_initialize_creates_schema(self, db_path):
        """Test that initialize creates the SQLite schema."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        assert db_path.exists()

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, db_path):
        """Test that calling initialize twice is safe."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()
        await cache.initialize()  # Should not raise

    @pytest.mark.asyncio
    async def test_set_and_get(self, db_path):
        """Test basic set and get."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        await cache.set("key1", "value1")
        result = await cache.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_miss_returns_none(self, db_path):
        """Test that get returns None for missing keys."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, db_path):
        """Test delete removes from both layers."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")

        assert deleted is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, db_path):
        """Test delete returns False for missing key."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        deleted = await cache.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_clear(self, db_path):
        """Test clear removes all entries from both layers."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_exists(self, db_path):
        """Test exists returns correct boolean."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        await cache.set("key1", "value1")

        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_l1_hit_fast_path(self, db_path):
        """Test L1 hit doesn't increment L2 hits."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        await cache.set("key1", "value1")
        await cache.get("key1")  # L1 hit

        stats = cache.stats()
        assert stats.hits == 1
        assert stats.l2_hits == 0

    @pytest.mark.asyncio
    async def test_l1_miss_l2_hit_promotes(self, db_path):
        """Test L1 miss falls back to L2 and promotes."""
        cache = PersistentCache(
            max_size=2, db_path=db_path, warm_on_init=False
        )
        await cache.initialize()

        # Fill cache and force eviction from L1
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")  # Evicts key1 from L1

        # key1 should still be in L2
        result = await cache.get("key1")
        assert result == "value1"

        stats = cache.stats()
        assert stats.l2_hits == 1

    @pytest.mark.asyncio
    async def test_l1_miss_l2_miss(self, db_path):
        """Test total miss when key is in neither layer."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        result = await cache.get("nonexistent")

        assert result is None
        stats = cache.stats()
        assert stats.hits == 0
        assert stats.l2_hits == 0
        assert stats.misses == 1

    @pytest.mark.asyncio
    async def test_set_writes_to_both_layers(self, db_path):
        """Test that set writes to L2 (survives L1 clear)."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        await cache.set("key1", "value1")

        # Clear only L1
        await cache._l1.clear()

        # Should still find in L2
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_ttl_expired_returns_none(self, db_path):
        """Test that expired entries return None."""
        import time
        from unittest.mock import patch

        cache = PersistentCache(
            default_ttl=1.0, db_path=db_path, warm_on_init=False
        )
        await cache.initialize()

        await cache.set("key1", "value1")

        # Advance time past TTL
        with patch("router.cache.memory.time") as mock_time, \
             patch("router.cache.persistent.time") as mock_ptime:
            future = time.time() + 5.0
            mock_time.time.return_value = future
            mock_ptime.time.return_value = future

            result = await cache.get("key1")
            assert result is None

    @pytest.mark.asyncio
    async def test_lru_eviction_preserves_l2(self, db_path):
        """Test that L1 eviction doesn't affect L2."""
        cache = PersistentCache(
            max_size=2, db_path=db_path, warm_on_init=False
        )
        await cache.initialize()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")  # Evicts key1 from L1

        # key1 evicted from L1 but still in L2
        l2_count = await cache.refresh_l2_size()
        assert l2_count == 3  # All 3 in L2

    @pytest.mark.asyncio
    async def test_survives_restart(self, db_path):
        """Test that cache data persists across instances."""
        # Instance 1: populate
        cache1 = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache1.initialize()
        await cache1.set("key1", "value1")
        await cache1.set("key2", "value2")
        await cache1.close()

        # Instance 2: read back
        cache2 = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache2.initialize()

        # L1 is empty, but L2 has data
        result = await cache2.get("key1")
        assert result == "value1"
        result = await cache2.get("key2")
        assert result == "value2"

    @pytest.mark.asyncio
    async def test_warm_l1_from_l2(self, db_path):
        """Test that L1 is warmed from L2 on init."""
        # Instance 1: populate L2
        cache1 = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache1.initialize()
        await cache1.set("key1", "value1")
        await cache1.set("key2", "value2")
        await cache1.close()

        # Instance 2: warm on init
        cache2 = PersistentCache(db_path=db_path, warm_on_init=True)
        await cache2.initialize()

        # Should be L1 hits (warmed), not L2 hits
        result = await cache2.get("key1")
        assert result == "value1"

        stats = cache2.stats()
        assert stats.hits == 1
        assert stats.l2_hits == 0  # Came from L1 warmup

    @pytest.mark.asyncio
    async def test_stats_hit_rate_includes_l2(self, db_path):
        """Test that hit_rate accounts for both L1 and L2 hits."""
        cache = PersistentCache(
            max_size=1, db_path=db_path, warm_on_init=False
        )
        await cache.initialize()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")  # Evicts key1 from L1

        await cache.get("key2")  # L1 hit
        await cache.get("key1")  # L2 hit (promoted)
        await cache.get("missing")  # Miss

        stats = cache.stats()
        assert stats.hits == 1
        assert stats.l2_hits == 1
        # hit_rate = (1 + 1) / (1 + 1 + 1) = 0.667
        assert abs(stats.hit_rate - 2 / 3) < 0.01

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, db_path):
        """Test cleanup_expired removes from both layers."""
        import time
        from unittest.mock import patch

        cache = PersistentCache(
            default_ttl=1.0, db_path=db_path, warm_on_init=False
        )
        await cache.initialize()

        await cache.set("key1", "value1")

        with patch("router.cache.memory.time") as mock_time, \
             patch("router.cache.persistent.time") as mock_ptime:
            future = time.time() + 5.0
            mock_time.time.return_value = future
            mock_ptime.time.return_value = future

            removed = await cache.cleanup_expired()
            assert removed >= 1

    @pytest.mark.asyncio
    async def test_json_serialization_roundtrip(self, db_path):
        """Test that complex values survive JSON serialization."""
        cache = PersistentCache(db_path=db_path, warm_on_init=False)
        await cache.initialize()

        complex_value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        await cache.set("key1", complex_value)

        # Clear L1 to force L2 read
        await cache._l1.clear()

        result = await cache.get("key1")
        assert result == complex_value


class TestPersistentEnhancementCache:
    """Tests for PersistentEnhancementCache."""

    @pytest.mark.asyncio
    async def test_get_enhanced_set_enhanced(self, db_path):
        """Test convenience API for enhancement caching."""
        cache = PersistentEnhancementCache(db_path=db_path)
        await cache.initialize()

        await cache.set_enhanced(
            prompt="help me code",
            enhanced="Help me write clean, well-structured code.",
            client_name="vscode",
            model="llama3.2:latest",
        )

        result = await cache.get_enhanced(
            prompt="help me code",
            client_name="vscode",
            model="llama3.2:latest",
        )
        assert result == "Help me write clean, well-structured code."

    @pytest.mark.asyncio
    async def test_get_enhanced_miss(self, db_path):
        """Test that missing enhancement returns None."""
        cache = PersistentEnhancementCache(db_path=db_path)
        await cache.initialize()

        result = await cache.get_enhanced(
            prompt="nonexistent", client_name="test"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_different_clients_different_keys(self, db_path):
        """Test that same prompt with different clients are separate."""
        cache = PersistentEnhancementCache(db_path=db_path)
        await cache.initialize()

        await cache.set_enhanced(
            prompt="help", enhanced="enhanced-vscode",
            client_name="vscode",
        )
        await cache.set_enhanced(
            prompt="help", enhanced="enhanced-raycast",
            client_name="raycast",
        )

        assert await cache.get_enhanced(
            "help", client_name="vscode"
        ) == "enhanced-vscode"
        assert await cache.get_enhanced(
            "help", client_name="raycast"
        ) == "enhanced-raycast"

    @pytest.mark.asyncio
    async def test_persistence_survives_restart(self, db_path):
        """Test enhancement cache survives instance restart."""
        # Instance 1
        cache1 = PersistentEnhancementCache(db_path=db_path)
        await cache1.initialize()
        await cache1.set_enhanced(
            prompt="test prompt",
            enhanced="improved test prompt",
            client_name="claude-desktop",
        )
        await cache1.close()

        # Instance 2
        cache2 = PersistentEnhancementCache(db_path=db_path)
        await cache2.initialize()

        result = await cache2.get_enhanced(
            prompt="test prompt",
            client_name="claude-desktop",
        )
        assert result == "improved test prompt"

    @pytest.mark.asyncio
    async def test_different_models_different_keys(self, db_path):
        """Test that same prompt with different models are separate."""
        cache = PersistentEnhancementCache(db_path=db_path)
        await cache.initialize()

        await cache.set_enhanced(
            prompt="help", enhanced="v1",
            model="llama3.2:latest",
        )
        await cache.set_enhanced(
            prompt="help", enhanced="v2",
            model="deepseek-r1:latest",
        )

        assert await cache.get_enhanced(
            "help", model="llama3.2:latest"
        ) == "v1"
        assert await cache.get_enhanced(
            "help", model="deepseek-r1:latest"
        ) == "v2"
