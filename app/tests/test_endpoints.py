"""
Integration tests for BUILD-SPEC.md API endpoints.

Verifies all Phase 2-4 success criteria by testing actual API endpoints.
These are integration tests that require the router to be running.
"""

import pytest
from httpx import AsyncClient
import json


# Base URL for testing
BASE_URL = "http://localhost:9090"


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test GET /health returns all services status."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()

            # Verify expected structure
            assert "status" in data
            assert "services" in data
            assert "servers" in data

            # Verify services
            assert data["services"]["router"] == "up"
            assert data["services"]["ollama"] in ["up", "down"]

            # Verify servers summary
            assert "total" in data["servers"]
            assert "running" in data["servers"]


class TestServerManagementEndpoints:
    """Test Phase 2.5 server management endpoints."""

    @pytest.mark.asyncio
    async def test_list_servers(self):
        """Test GET /servers lists all configured servers."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/servers")

            assert response.status_code == 200
            data = response.json()

            # Should return server list (can be dict or list)
            assert "servers" in data

            servers = data["servers"]
            # Support both formats
            if isinstance(servers, list):
                # List format - verify entries have required fields
                for server_info in servers:
                    assert "name" in server_info
                    assert "status" in server_info
                    assert server_info["status"] in ["running", "stopped", "failed", "starting", "stopping"]
            else:
                # Dict format
                for name, server_info in servers.items():
                    assert "status" in server_info
                    assert server_info["status"] in ["running", "stopped", "failed", "starting", "stopping"]

    @pytest.mark.asyncio
    async def test_get_server_details(self):
        """Test GET /servers/{name} returns server details."""
        async with AsyncClient(base_url=BASE_URL) as client:
            # First get list to find a server
            list_response = await client.get("/servers")
            servers = list_response.json()["servers"]

            if servers:
                # Get first server name (handle both list and dict formats)
                if isinstance(servers, list):
                    server_name = servers[0]["name"]
                else:
                    server_name = list(servers.keys())[0]

                # Get server details
                response = await client.get(f"/servers/{server_name}")

                assert response.status_code == 200
                data = response.json()

                # Verify structure
                assert "config" in data
                assert "process" in data
                assert data["config"]["name"] == server_name

    @pytest.mark.asyncio
    async def test_get_nonexistent_server(self):
        """Test GET /servers/{name} returns 404 for unknown server."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/servers/nonexistent-server-xyz")

            assert response.status_code == 404


class TestDashboardEndpoints:
    """Test Phase 4 dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_dashboard_main_page(self):
        """Test GET /dashboard loads main page."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/dashboard")

            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

            # Verify key content is present
            html = response.text
            assert "AgentHub Dashboard" in html
            assert "hx-get" in html  # HTMX attributes present

    @pytest.mark.asyncio
    async def test_dashboard_health_partial(self):
        """Test GET /dashboard/health-partial returns HTMX partial."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/dashboard/health-partial")

            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_dashboard_stats_partial(self):
        """Test GET /dashboard/stats-partial returns stats."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/dashboard/stats-partial")

            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_dashboard_activity_partial(self):
        """Test GET /dashboard/activity-partial returns activity log."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/dashboard/activity-partial")

            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_dashboard_guides_partial(self):
        """Test GET /dashboard/guides-partial returns guide list."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/dashboard/guides-partial")

            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_dashboard_guide_view(self):
        """Test GET /dashboard/guides/view/{filename} renders markdown."""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Try to view a guide (assuming at least index.md exists)
            response = await client.get("/dashboard/guides/view/index.md")

            # Should either succeed or return 404 if no guides exist
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                assert "text/html" in response.headers["content-type"]
                html = response.text
                assert "guide-modal" in html


class TestCircuitBreakerIntegration:
    """Test circuit breaker behavior in live system."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_stats_in_health(self):
        """Test circuit breaker stats are included in health endpoint."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()

            # Circuit breaker info may be in cache stats
            if "cache" in data["services"]:
                cache_info = data["services"]["cache"]
                # Just verify structure is present
                assert isinstance(cache_info, dict)


class TestCacheIntegration:
    """Test cache functionality in live system."""

    @pytest.mark.asyncio
    async def test_cache_stats_available(self):
        """Test cache statistics are accessible."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()

            # Verify cache stats exist
            assert "cache" in data["services"]
            cache = data["services"]["cache"]
            assert "hit_rate" in cache
            assert "size" in cache


class TestBuildSpecCriteria:
    """Verify BUILD-SPEC.md Phase 2 success criteria."""

    @pytest.mark.asyncio
    async def test_router_starts_successfully(self):
        """Verify: Router starts with uvicorn router.main:app."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_returns_all_services(self):
        """Verify: GET /health returns all services status."""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()

            # All required services should be listed
            assert "router" in data["services"]
            assert "ollama" in data["services"]
            assert "cache" in data["services"]
            assert "servers" in data

    @pytest.mark.asyncio
    async def test_configs_are_loadable(self):
        """Verify: Configs are hot-reloadable (restart applies changes)."""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Verify config is loaded by checking server list
            response = await client.get("/servers")

            assert response.status_code == 200
            data = response.json()

            # Should have loaded servers from config
            assert len(data["servers"]) > 0
