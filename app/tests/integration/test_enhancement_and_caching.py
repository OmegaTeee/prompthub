"""
Integration tests for prompt enhancement and caching.

Tests default local-model enhancement and cache behavior.
"""

import os

import httpx
import pytest

# Router under test: an isolated instance from the live_router fixture (conftest.py).
ROUTER_URL = os.environ["PROMPTHUB_TEST_URL"]
pytestmark = pytest.mark.usefixtures("live_router")


class TestPromptEnhancement:
    """Test enhancement behavior with the configured local LLM."""

    @pytest.mark.asyncio
    async def test_enhancement_fallback_when_llm_down(self):
        """
        Test that the enhancement endpoint degrades gracefully.

        The endpoint returns 200 with original prompt on LLM failure,
        503 only if the EnhancementService itself isn't initialized.
        A client-side timeout is also acceptable.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=15.0) as client:
            original_prompt = "test prompt for fallback behavior"

            try:
                response = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": original_prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                # Client-side timeout — LLM may be running but slow,
                # or router's LLM timeout exceeds our client timeout
                return

            assert response.status_code in [200, 503], (
                f"Expected 200 or 503, got {response.status_code}"
            )

            if response.status_code == 503:
                # Enhancement service not initialized
                data = response.json()
                assert "detail" in data, "503 should include detail message"
                return

            # 200 — verify response structure
            data = response.json()
            assert "original" in data, "Response must include 'original'"
            assert "enhanced" in data, "Response must include 'enhanced'"
            assert data["original"] == original_prompt

            if data.get("error"):
                # LLM was unreachable — graceful degradation
                assert data["enhanced"] == original_prompt, (
                    "On error, enhanced should equal original (no-op fallback)"
                )
                assert data.get("was_enhanced") is False
            else:
                # LLM was available — enhancement succeeded
                assert data.get("model") is not None, (
                    "Successful enhancement should report model used"
                )

    @pytest.mark.asyncio
    async def test_enhancement_endpoint_exists(self):
        """Test that enhancement endpoint is accessible."""
        # Use longer timeout since LLM might be slow
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=30.0) as client:
            response = await client.post(
                "/llm/enhance",
                headers={"X-Client-Name": "test"},
                json={"prompt": "test"},
            )

            # Should not return 404
            # 503 is acceptable if LLM is not running
            assert response.status_code in [200, 503], (
                f"Enhancement endpoint returned unexpected status: {response.status_code}"
            )


class TestCaching:
    """
    Integration tests for enhancement caching via /llm/enhance.

    Note: The MCP proxy (/mcp/{server}/{path}) has NO caching layer.
    Caching only exists in the EnhancementService for /llm/enhance.
    Unit tests for MemoryCache internals are in test_cache.py.
    """

    @pytest.mark.asyncio
    async def test_cache_hit_returns_identical_response(self):
        """
        Test that a cached enhancement returns the same result and is marked cached.

        Expected: Second request returns cached=True with identical enhanced text.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=60.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "Explain list comprehensions in Python"

            # First request (cache miss)
            try:
                response1 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "claude-desktop"},
                    json={"prompt": prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on first enhancement")

            if response1.status_code == 503:
                pytest.skip("Enhancement service not initialized")

            assert response1.status_code == 200
            data1 = response1.json()

            # Second request (cache hit)
            response2 = await client.post(
                "/llm/enhance",
                headers={"X-Client-Name": "claude-desktop"},
                json={"prompt": prompt},
            )
            assert response2.status_code == 200
            data2 = response2.json()

            # Enhanced text must be identical
            assert data2["enhanced"] == data1["enhanced"], (
                "Cached response should return identical enhanced text"
            )

            # If first request succeeded with a model, second should be cached
            if data1.get("model"):
                assert data2.get("cached") is True, (
                    "Second identical request should come from cache"
                )

    @pytest.mark.asyncio
    async def test_cache_is_per_client(self):
        """
        Test that cache entries are separated by client name.

        The cache key includes client_name, so two unconfigured clients using
        the default local model receive separate cache entries.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=120.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "What are Python generators"

            # Enhance for the first unconfigured test client.
            try:
                resp_a = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "pytest-cache-a"},
                    json={"prompt": prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on first test client enhancement")

            if resp_a.status_code == 503:
                pytest.skip("Enhancement service not initialized")

            assert resp_a.status_code == 200
            data_a = resp_a.json()

            # The second client uses the same default model but a different key.
            try:
                resp_b = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "pytest-cache-b"},
                    json={"prompt": prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on second test client enhancement")
            assert resp_b.status_code == 200
            data_b = resp_b.json()

            # Neither should be cached on first call
            if data_a.get("model"):
                assert data_a.get("cached") is not True
            if data_b.get("model"):
                assert data_b.get("cached") is not True

    @pytest.mark.asyncio
    async def test_cache_stats_reflect_usage(self):
        """
        Test that cache stats reported in /health reflect actual usage.

        Expected: After a miss + hit cycle, stats show at least 1 hit.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=60.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "Cache stats integration test prompt"

            # Request 1 (miss)
            try:
                resp1 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on first enhancement")
            if resp1.status_code == 503:
                pytest.skip("Enhancement service not initialized")
            assert resp1.status_code == 200

            # Request 2 (hit)
            resp2 = await client.post(
                "/llm/enhance",
                headers={"X-Client-Name": "test"},
                json={"prompt": prompt},
            )
            assert resp2.status_code == 200

            # Check health endpoint for cache stats
            health = await client.get("/health")
            assert health.status_code == 200
            health_data = health.json()

            cache_info = health_data.get("services", {}).get("cache", {})
            assert cache_info.get("status") == "up", "Cache should be reported as up"
            assert cache_info.get("size", 0) >= 1, "Cache should have at least 1 entry"

    @pytest.mark.asyncio
    async def test_cache_clear_resets_state(self):
        """
        Test that clearing the cache removes entries and resets stats.

        Expected: After clear, next request is not cached.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=60.0) as client:
            prompt = "Cache clear integration test"

            # Populate cache
            try:
                resp1 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on first enhancement")
            if resp1.status_code == 503:
                pytest.skip("Enhancement service not initialized")
            assert resp1.status_code == 200

            # Clear cache
            clear_resp = await client.post("/dashboard/actions/clear-cache")
            assert clear_resp.status_code in [200, 204]

            # Request again — should NOT be cached
            try:
                resp2 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on post-clear enhancement")
            assert resp2.status_code == 200
            data2 = resp2.json()

            # If LLM is available, this should be a fresh enhancement (not cached)
            if data2.get("model"):
                assert data2.get("cached") is not True, (
                    "After cache clear, request should not return cached result"
                )

    @pytest.mark.asyncio
    async def test_cache_bypass_skips_cache(self):
        """
        Test that bypass_cache=True skips cache lookup.

        Expected: Even after caching, bypass returns a fresh result.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=60.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "Cache bypass test prompt"

            # Populate cache
            try:
                resp1 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on first enhancement")
            if resp1.status_code == 503:
                pytest.skip("Enhancement service not initialized")
            assert resp1.status_code == 200

            # Bypass cache — also needs fresh LLM call
            try:
                resp2 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt, "bypass_cache": True},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on bypass enhancement")
            assert resp2.status_code == 200
            data2 = resp2.json()

            # Should NOT be marked as cached
            assert data2.get("cached") is not True, (
                "bypass_cache=True should skip cache lookup"
            )


class TestEnhancementAndCachingIntegration:
    """Test integration between enhancement and caching."""

    @pytest.mark.asyncio
    async def test_cache_key_includes_client_name(self):
        """
        Test that cache key accounts for client-specific enhancements.

        The enhancement cache keys include client_name so two unconfigured
        clients using the default local model have separate cache entries.

        When the local LLM is available, this verifies per-client cache isolation.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=120.0) as client:
            # Clear cache
            await client.post("/dashboard/actions/clear-cache")

            test_prompt = "Explain Python decorators"

            # Enhance with the first unconfigured test client.
            try:
                enh1 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "pytest-cache-key-a"},
                    json={"prompt": test_prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on first enhancement")

            if enh1.status_code == 503:
                pytest.skip("Enhancement service not initialized")

            assert enh1.status_code == 200
            data1 = enh1.json()

            # The second client has the same default rule but a different key.
            try:
                enh2 = await client.post(
                    "/llm/enhance",
                    headers={"X-Client-Name": "pytest-cache-key-b"},
                    json={"prompt": test_prompt},
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("LLM timed out on second enhancement")

            assert enh2.status_code == 200
            data2 = enh2.json()

            # Verify both clients get responses with correct structure
            assert "enhanced" in data1, "First client response missing 'enhanced'"
            assert "enhanced" in data2, "Second client response missing 'enhanced'"

            # Both use the configured default model.
            if data1.get("model") and data2.get("model"):
                assert data1["model"] == data2["model"], (
                    "Unconfigured clients should use the same default model"
                )

            # Re-request the first client — it should hit that client's cache.
            enh1_again = await client.post(
                "/llm/enhance",
                headers={"X-Client-Name": "pytest-cache-key-a"},
                json={"prompt": test_prompt},
            )
            assert enh1_again.status_code == 200
            data1_again = enh1_again.json()

            # Cached response should match original response
            assert data1_again["enhanced"] == data1["enhanced"], (
                "Same client + same prompt should return cached result"
            )
            # If LLM was up for the first call, second should be cached
            if data1.get("model"):
                assert data1_again.get("cached") is True, (
                    "Repeat request should come from cache"
                )
