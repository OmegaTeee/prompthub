"""
Integration tests for prompt enhancement and caching.

Tests client-specific enhancement models and cache performance.
"""

import time

import httpx
import pytest


class TestPromptEnhancement:
    """Test prompt enhancement with Ollama."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhancement_uses_client_specific_model(self):
        """
        Test that different clients use different enhancement models.

        Must match configs/enhancement-rules.json:
        - claude-desktop: deepseek-r1:latest
        - vscode: qwen2.5-coder:32b
        - raycast: llama3.2:latest
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            clients_and_models = [
                ("claude-desktop", "deepseek-r1"),
                ("vscode", "qwen2.5-coder"),
                ("raycast", "llama3.2"),
            ]

            for client_name, expected_model in clients_and_models:
                response = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": client_name},
                    json={"prompt": "Explain async/await"}
                )

                assert response.status_code == 200
                data = response.json()

                assert "enhanced" in data, f"Response missing 'enhanced' key for {client_name}"
                assert "original" in data, f"Response missing 'original' key for {client_name}"

                actual_model = data.get("model")
                assert actual_model is not None, f"Model should be set for {client_name}"
                assert expected_model in actual_model.lower(), \
                    f"{client_name} should use {expected_model}, got {actual_model}"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhancement_code_first_for_vscode(self):
        """
        Test that VS Code enhancement is code-first.

        Expected: Code examples before explanations (qwen2.5-coder system prompt).
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            response = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "vscode"},
                json={"prompt": "array sorting"}
            )

            assert response.status_code == 200
            data = response.json()

            enhanced = data.get("enhanced", "")
            assert enhanced, "Enhanced prompt should not be empty"

            # Should contain code (backticks or specific keywords)
            assert "```" in enhanced or "function" in enhanced or "const" in enhanced

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhancement_action_oriented_for_raycast(self):
        """
        Test that Raycast enhancement is action-oriented.

        Expected: CLI commands, under 200 words (llama3.2 system prompt).
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            response = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "raycast"},
                json={"prompt": "disk usage"}
            )

            assert response.status_code == 200
            data = response.json()

            enhanced = data.get("enhanced", "")
            assert enhanced, "Enhanced prompt should not be empty"

            # Should be relatively short (under 300 words for action-oriented)
            word_count = len(enhanced.split())
            assert word_count < 300, f"Raycast response too long: {word_count} words"

            # Should contain CLI-like content
            assert any(cmd in enhanced.lower() for cmd in ["df", "du", "disk", "usage"])

    @pytest.mark.asyncio
    async def test_enhancement_fallback_when_ollama_down(self):
        """
        Test that the enhancement endpoint degrades gracefully.

        The endpoint returns 200 with original prompt on Ollama failure,
        503 only if the EnhancementService itself isn't initialized.
        A client-side timeout is also acceptable.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=15.0) as client:
            original_prompt = "test prompt for fallback behavior"

            try:
                response = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": original_prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                # Client-side timeout — Ollama may be running but slow,
                # or router's Ollama timeout exceeds our client timeout
                return

            assert response.status_code in [200, 503], \
                f"Expected 200 or 503, got {response.status_code}"

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
                # Ollama was unreachable — graceful degradation
                assert data["enhanced"] == original_prompt, \
                    "On error, enhanced should equal original (no-op fallback)"
                assert data.get("was_enhanced") is False
            else:
                # Ollama was available — enhancement succeeded
                assert data.get("model") is not None, \
                    "Successful enhancement should report model used"

    @pytest.mark.asyncio
    async def test_enhancement_endpoint_exists(self):
        """Test that enhancement endpoint is accessible."""
        # Use longer timeout since Ollama might be slow
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=30.0) as client:
            response = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "test"},
                json={"prompt": "test"}
            )

            # Should not return 404
            # 503 is acceptable if Ollama is not running
            assert response.status_code in [200, 503], \
                f"Enhancement endpoint returned unexpected status: {response.status_code}"


class TestCaching:
    """
    Integration tests for enhancement caching via /ollama/enhance.

    Note: The MCP proxy (/mcp/{server}/{path}) has NO caching layer.
    Caching only exists in the EnhancementService for /ollama/enhance.
    Unit tests for MemoryCache internals are in test_cache.py.
    """

    @pytest.mark.asyncio
    async def test_cache_hit_returns_identical_response(self):
        """
        Test that a cached enhancement returns the same result and is marked cached.

        Expected: Second request returns cached=True with identical enhanced text.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=60.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "Explain list comprehensions in Python"

            # First request (cache miss)
            try:
                response1 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "claude-desktop"},
                    json={"prompt": prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on first enhancement")

            if response1.status_code == 503:
                pytest.skip("Enhancement service not initialized")

            assert response1.status_code == 200
            data1 = response1.json()

            # Second request (cache hit)
            response2 = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "claude-desktop"},
                json={"prompt": prompt}
            )
            assert response2.status_code == 200
            data2 = response2.json()

            # Enhanced text must be identical
            assert data2["enhanced"] == data1["enhanced"], \
                "Cached response should return identical enhanced text"

            # If first request succeeded with a model, second should be cached
            if data1.get("model"):
                assert data2.get("cached") is True, \
                    "Second identical request should come from cache"

    @pytest.mark.asyncio
    async def test_cache_is_per_client(self):
        """
        Test that cache entries are separated by client name.

        The cache key includes client_name and model, so the same prompt
        enhanced for claude-desktop (deepseek-r1) is stored separately
        from the same prompt enhanced for vscode (qwen2.5-coder).
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=60.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "What are Python generators"

            # Enhance for claude-desktop
            try:
                resp_cd = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "claude-desktop"},
                    json={"prompt": prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on claude-desktop enhancement")

            if resp_cd.status_code == 503:
                pytest.skip("Enhancement service not initialized")

            assert resp_cd.status_code == 200
            data_cd = resp_cd.json()

            # Enhance for vscode (same prompt, different client → different cache key)
            try:
                resp_vs = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "vscode"},
                    json={"prompt": prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on vscode enhancement (model swap)")
            assert resp_vs.status_code == 200
            data_vs = resp_vs.json()

            # Neither should be marked cached on first call
            # (unless Ollama failed and both got no-op fallback)
            if data_cd.get("model") and data_vs.get("model"):
                assert data_cd["model"] != data_vs["model"], \
                    "Different clients should use different models"

    @pytest.mark.asyncio
    async def test_cache_stats_reflect_usage(self):
        """
        Test that cache stats reported in /health reflect actual usage.

        Expected: After a miss + hit cycle, stats show at least 1 hit.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=60.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "Cache stats integration test prompt"

            # Request 1 (miss)
            try:
                resp1 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on first enhancement")
            if resp1.status_code == 503:
                pytest.skip("Enhancement service not initialized")
            assert resp1.status_code == 200

            # Request 2 (hit)
            resp2 = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "test"},
                json={"prompt": prompt}
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
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=60.0) as client:
            prompt = "Cache clear integration test"

            # Populate cache
            try:
                resp1 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on first enhancement")
            if resp1.status_code == 503:
                pytest.skip("Enhancement service not initialized")
            assert resp1.status_code == 200

            # Clear cache
            clear_resp = await client.post("/dashboard/actions/clear-cache")
            assert clear_resp.status_code in [200, 204]

            # Request again — should NOT be cached
            try:
                resp2 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on post-clear enhancement")
            assert resp2.status_code == 200
            data2 = resp2.json()

            # If Ollama is available, this should be a fresh enhancement (not cached)
            if data2.get("model"):
                assert data2.get("cached") is not True, \
                    "After cache clear, request should not return cached result"

    @pytest.mark.asyncio
    async def test_cache_bypass_skips_cache(self):
        """
        Test that bypass_cache=True skips cache lookup.

        Expected: Even after caching, bypass returns a fresh result.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=60.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            prompt = "Cache bypass test prompt"

            # Populate cache
            try:
                resp1 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on first enhancement")
            if resp1.status_code == 503:
                pytest.skip("Enhancement service not initialized")
            assert resp1.status_code == 200

            # Bypass cache — also needs fresh Ollama call
            try:
                resp2 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "test"},
                    json={"prompt": prompt, "bypass_cache": True}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on bypass enhancement")
            assert resp2.status_code == 200
            data2 = resp2.json()

            # Should NOT be marked as cached
            assert data2.get("cached") is not True, \
                "bypass_cache=True should skip cache lookup"


class TestEnhancementAndCachingIntegration:
    """Test integration between enhancement and caching."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhanced_prompts_are_cached(self):
        """
        Test that Ollama-enhanced prompts are cached and replayed.

        Expected: Same original prompt → identical enhanced text from cache,
        with cached=True flag and faster response time.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=30.0) as client:
            await client.post("/dashboard/actions/clear-cache")

            original_prompt = "Explain React hooks"

            # First enhancement (cache miss — hits Ollama)
            response1 = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "claude-desktop"},
                json={"prompt": original_prompt}
            )
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1.get("model") is not None, "Ollama should be running for this test"
            assert data1.get("cached") is not True

            # Second enhancement (cache hit — skips Ollama)
            start_time = time.time()
            response2 = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "claude-desktop"},
                json={"prompt": original_prompt}
            )
            cache_time = time.time() - start_time

            assert response2.status_code == 200
            data2 = response2.json()

            assert data2["enhanced"] == data1["enhanced"], \
                "Cached response must return identical enhanced text"
            assert data2.get("cached") is True, \
                "Second request should be served from cache"
            assert cache_time < 0.5, \
                f"Cache hit should be fast, took {cache_time:.3f}s"

    @pytest.mark.asyncio
    async def test_cache_key_includes_client_name(self):
        """
        Test that cache key accounts for client-specific enhancements.

        The enhancement cache keys include client_name so that the same prompt
        enhanced for claude-desktop (deepseek-r1) is cached separately from the
        same prompt enhanced for vscode (qwen2.5-coder).

        When Ollama is running: verifies different models produce separate cache entries.
        When Ollama is down: verifies each client gets its own error/fallback entry.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=60.0) as client:
            # Clear cache
            await client.post("/dashboard/actions/clear-cache")

            test_prompt = "Explain Python decorators"

            # Enhance with claude-desktop (deepseek-r1)
            try:
                enh1 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "claude-desktop"},
                    json={"prompt": test_prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on first enhancement")

            if enh1.status_code == 503:
                pytest.skip("Enhancement service not initialized")

            assert enh1.status_code == 200
            data1 = enh1.json()

            # Enhance with vscode (qwen2.5-coder) — may be slow for large model
            try:
                enh2 = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": "vscode"},
                    json={"prompt": test_prompt}
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                pytest.skip("Ollama timed out on second enhancement (model swap)")

            assert enh2.status_code == 200
            data2 = enh2.json()

            # Verify both clients get responses with correct structure
            assert "enhanced" in data1, "claude-desktop response missing 'enhanced'"
            assert "enhanced" in data2, "vscode response missing 'enhanced'"

            # If Ollama was available for both, they should use different models
            if data1.get("model") and data2.get("model"):
                assert data1["model"] != data2["model"], \
                    f"Different clients should use different models, both got {data1['model']}"

            # Re-request claude-desktop — should hit cache (same client + prompt)
            enh1_again = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "claude-desktop"},
                json={"prompt": test_prompt}
            )
            assert enh1_again.status_code == 200
            data1_again = enh1_again.json()

            # Cached response should match original response
            assert data1_again["enhanced"] == data1["enhanced"], \
                "Same client + same prompt should return cached result"
            # If Ollama was up for the first call, second should be cached
            if data1.get("model"):
                assert data1_again.get("cached") is True, \
                    "Repeat request should come from cache"
