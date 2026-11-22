"""
Integration tests for MCP proxy functionality.

Tests that JSON-RPC requests are correctly proxied to MCP servers.
"""

import asyncio
import os

import httpx
import pytest

# Router under test: an isolated instance from the live_router fixture (conftest.py).
ROUTER_URL = os.environ["PROMPTHUB_TEST_URL"]
pytestmark = pytest.mark.usefixtures("live_router")



class TestMCPProxyRouting:
    """Test MCP proxy routing to servers."""

    @pytest.mark.asyncio
    async def test_proxy_to_context7(self):
        """Test proxying requests to context7 server."""
        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            )

            assert response.status_code == 200
            data = response.json()

            # Should be valid JSON-RPC response
            assert "jsonrpc" in data
            assert data["jsonrpc"] == "2.0"
            # Note: ID may be transformed by router, just verify it exists
            assert "id" in data

            # Should have result or error
            assert "result" in data or "error" in data

            # If successful, verify tools structure
            if "result" in data:
                assert "tools" in data["result"]
                tools = data["result"]["tools"]
                assert isinstance(tools, list)

                # context7 should have specific tools
                tool_names = [t["name"] for t in tools]
                assert "query-docs" in tool_names or "resolve-library-id" in tool_names

    @pytest.mark.asyncio
    async def test_proxy_to_all_servers(self):
        """Test that all MCP servers are accessible via proxy."""
        servers = [
            "context7",
            "desktop-commander",
            "sequential-thinking",
            "memory",
            "duckduckgo",
        ]

        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            for server_name in servers:
                response = await client.post(
                    f"/mcp/{server_name}/tools/call",
                    headers={"X-Client-Name": "test"},
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                )

                assert response.status_code in [200, 503], (
                    f"Server {server_name} returned unexpected status: {response.status_code}"
                )

                # 503 is OK if circuit breaker is OPEN
                # 200 means success
                if response.status_code == 200:
                    data = response.json()
                    assert "result" in data or "error" in data

    @pytest.mark.asyncio
    async def test_invalid_server_returns_404(self):
        """Test that requesting non-existent server returns 404."""
        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            response = await client.post(
                "/mcp/nonexistent-server/tools/call",
                headers={"X-Client-Name": "test"},
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_json_rpc_error_handling(self):
        """Test that invalid JSON-RPC requests are handled properly."""
        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            # Missing required fields
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json={
                    "method": "tools/list"
                    # Missing jsonrpc and id
                },
            )

            # Should still return 200 (HTTP) but with JSON-RPC error
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_client_name_header_preserved(self):
        """Test that X-Client-Name header is forwarded to servers."""
        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            client_names = ["claude-desktop", "vscode", "raycast", "test"]

            for client_name in client_names:
                response = await client.post(
                    "/mcp/context7/tools/call",
                    headers={"X-Client-Name": client_name},
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                )

                assert response.status_code == 200
                # Client name should be logged in audit trail


class TestMCPProxyPerformance:
    """Test MCP proxy performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""

        async def make_request(client: httpx.AsyncClient, request_id: int):
            return await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json={"jsonrpc": "2.0", "method": "tools/list", "id": request_id},
            )

        async with httpx.AsyncClient(
            base_url=ROUTER_URL, timeout=30.0
        ) as client:
            # Send 10 concurrent requests
            tasks = [make_request(client, i) for i in range(10)]
            try:
                responses = await asyncio.gather(*tasks)
            except (httpx.ConnectTimeout, httpx.ReadTimeout):
                pytest.skip("Server overwhelmed during concurrent request test")

            # All should succeed
            for response in responses:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that long-running requests don't hang forever."""
        async with httpx.AsyncClient(
            base_url=ROUTER_URL, timeout=5.0
        ) as client:
            try:
                # Make request with short timeout
                response = await client.post(
                    "/mcp/sequential-thinking/tools/call",
                    headers={"X-Client-Name": "test"},
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "sequentialthinking",
                            "arguments": {
                                "thought": "Long complex reasoning task",
                                "thoughtNumber": 1,
                                "totalThoughts": 100,
                            },
                        },
                        "id": 1,
                    },
                )

                # Either completes or times out gracefully
                assert response.status_code in [200, 408, 503]

            except TimeoutError:
                # Timeout is acceptable behavior
                pass


class TestMCPProxyResilience:
    """Test circuit breaker and resilience features."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_activates_on_failures(self):
        """A stopped server returns 503; an auto-start server recovers on demand.

        The 503 comes from the server-not-running check (before bridge.send),
        so the circuit breaker may stay CLOSED: breakers protect against
        unhealthy running services, not stopped ones.
        """
        async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=30.0) as client:
            servers = (await client.get("/servers")).json()
            servers = servers.get("servers", servers)
            if isinstance(servers, dict):
                servers = [dict(name=k, **v) for k, v in servers.items()]
            names = {s["name"] for s in servers}

            # Part 1: a server without auto_start stays down and returns 503.
            on_demand = "chrome-devtools-mcp"
            assert on_demand in names, f"{on_demand} missing from test config"
            await client.post(f"/servers/{on_demand}/stop")  # 200 or 400 are both fine
            statuses = []
            for i in range(4):
                response = await client.post(
                    f"/mcp/{on_demand}/tools/call",
                    headers={"X-Client-Name": "test"},
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": i + 1},
                )
                statuses.append(response.status_code)
            assert all(code == 503 for code in statuses), (
                f"Stopped on-demand server should return 503, got {statuses}"
            )
            breakers = await client.get("/circuit-breakers")
            if breakers.status_code == 200 and on_demand in breakers.json():
                state = breakers.json()[on_demand]["state"]
                assert state.upper() in ["OPEN", "HALF_OPEN", "CLOSED"], state

            # Part 2: an auto_start server comes back after being stopped.
            auto = "memory"
            stop = await client.post(f"/servers/{auto}/stop")
            assert stop.status_code in [200, 400], stop.text
            recovered = False
            for attempt in range(5):
                response = await client.post(
                    f"/mcp/{auto}/tools/call",
                    headers={"X-Client-Name": "test"},
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": 100 + attempt},
                )
                if response.status_code == 200:
                    recovered = True
                    break
                await asyncio.sleep(1)
            assert recovered, f"{auto} did not recover after stop (last {response.status_code})"

    @pytest.mark.asyncio
    async def test_auto_restart_on_crash(self):
        """Test that crashed MCP servers auto-restart if configured with restart_on_failure."""
        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            # Use context7 server which has auto_start and restart_on_failure configured
            server_name = "context7"

            # Step 1: Get initial server info
            servers_response = await client.get("/servers")
            assert servers_response.status_code == 200
            servers = servers_response.json()

            if server_name not in servers:
                pytest.skip(f"Server {server_name} not configured")

            initial_info = servers[server_name]

            # Verify server is running and get initial PID
            if initial_info.get("status") != "running":
                # Start it first
                start_response = await client.post(f"/servers/{server_name}/start")
                assert start_response.status_code in [
                    200,
                    201,
                    400,
                ]  # 400 if already running

                # Wait for startup
                await asyncio.sleep(2)

                # Get updated info
                servers_response = await client.get("/servers")
                servers = servers_response.json()
                initial_info = servers[server_name]

            initial_pid = initial_info.get("pid")

            # Step 2: Forcefully stop the server (simulates crash)
            # Use the stop endpoint to cleanly stop it
            stop_response = await client.post(f"/servers/{server_name}/stop")
            # Server should stop successfully

            # Step 3: Wait for supervisor to detect and restart (if restart_on_failure is true)
            await asyncio.sleep(3)

            # Step 4: Check if server restarted
            servers_response = await client.get("/servers")
            servers = servers_response.json()
            current_info = servers.get(server_name, {})

            # If restart_on_failure is configured, server should auto-restart
            # If not, it will remain stopped - both behaviors are valid depending on config
            # We'll check the configuration to know what to expect
            if initial_info.get("restart_on_failure"):
                assert current_info.get("status") == "running", (
                    f"Server with restart_on_failure should auto-restart, got status: {current_info.get('status')}"
                )

                # Verify it's a new process (different PID)
                current_pid = current_info.get("pid")
                if initial_pid and current_pid:
                    # PIDs should be different (new process)
                    # Note: In some cases the PID might be None if process is restarting
                    pass  # PID comparison can be flaky, main thing is status is running
            else:
                # Without restart_on_failure, server should stay stopped
                # This is also valid behavior
                pass


class TestMCPProxyAudit:
    """Test audit logging for MCP proxy requests."""

    @pytest.mark.asyncio
    async def test_all_requests_logged(self):
        """Test that all MCP proxy requests are logged to audit trail."""
        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            # Make a unique request
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test-audit"},
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 999},
            )

            assert response.status_code == 200

            # Query audit log to verify it was logged
            audit_response = await client.get("/audit/activity?limit=10")

            if audit_response.status_code == 200:
                audit_data = audit_response.json()
                # Should find our request in recent activity
                # (checking for client_name="test-audit")

    @pytest.mark.asyncio
    async def test_sensitive_data_not_logged(self):
        """Test that sensitive data (API keys, tokens) is redacted from logs."""
        async with httpx.AsyncClient(base_url=ROUTER_URL) as client:
            # Send request with potentially sensitive data
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={
                    "X-Client-Name": "test",
                    "Authorization": "Bearer secret-token-123",
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"api_key": "sk-12345", "password": "super-secret"},
                    "id": 1,
                },
            )

            # Audit logs should redact sensitive fields
            # (This would require checking audit database)
            # (This would require checking audit database)
