"""
Tests for MCP gateway dynamic proxy factory.

Verifies that the gateway uses dynamic client factories to resolve
the current bridge at request time, not a captured client instance.
"""

import pytest
from unittest.mock import MagicMock, patch

from router.servers.mcp_gateway import _make_client_factory, build_mcp_gateway


class TestMakeClientFactory:
    """Test the dynamic client factory."""

    def test_returns_client_when_bridge_connected(self):
        """Factory should return bridge.client when bridge is connected."""
        mock_client = MagicMock()
        mock_bridge = MagicMock()
        mock_bridge.is_connected = True
        mock_bridge.client = mock_client

        mock_supervisor = MagicMock()
        mock_supervisor.get_bridge.return_value = mock_bridge

        factory = _make_client_factory(mock_supervisor, "test-server")
        result = factory()

        assert result is mock_client
        mock_supervisor.get_bridge.assert_called_with("test-server")

    def test_raises_when_no_bridge(self):
        """Factory should raise RuntimeError when no bridge exists."""
        mock_supervisor = MagicMock()
        mock_supervisor.get_bridge.return_value = None

        factory = _make_client_factory(mock_supervisor, "test-server")

        with pytest.raises(RuntimeError, match="not running"):
            factory()

    def test_raises_when_bridge_disconnected(self):
        """Factory should raise RuntimeError when bridge is disconnected."""
        mock_bridge = MagicMock()
        mock_bridge.is_connected = False

        mock_supervisor = MagicMock()
        mock_supervisor.get_bridge.return_value = mock_bridge

        factory = _make_client_factory(mock_supervisor, "test-server")

        with pytest.raises(RuntimeError, match="not running"):
            factory()

    def test_resolves_fresh_bridge_after_restart(self):
        """Factory should return new client after server restart."""
        old_client = MagicMock()
        new_client = MagicMock()

        old_bridge = MagicMock()
        old_bridge.is_connected = True
        old_bridge.client = old_client

        new_bridge = MagicMock()
        new_bridge.is_connected = True
        new_bridge.client = new_client

        mock_supervisor = MagicMock()
        mock_supervisor.get_bridge.side_effect = [old_bridge, new_bridge]

        factory = _make_client_factory(mock_supervisor, "test-server")

        assert factory() is old_client
        assert factory() is new_client


class TestBuildMcpGateway:
    """Test gateway construction with dynamic proxies."""

    @patch("router.servers.mcp_gateway.FastMCPProxy")
    def test_mounts_all_configured_servers(self, MockProxy):
        """Gateway should mount a proxy for every server in registry."""
        mock_supervisor = MagicMock()
        mock_registry = MagicMock()

        states = []
        for name in ["server-a", "server-b", "server-c"]:
            state = MagicMock()
            state.config.name = name
            states.append(state)
        mock_registry.list_all.return_value = states

        MockProxy.return_value = MagicMock()

        build_mcp_gateway(mock_supervisor, mock_registry)

        assert MockProxy.call_count == 3

    @patch("router.servers.mcp_gateway.FastMCPProxy")
    def test_mounts_disconnected_servers(self, MockProxy):
        """Gateway should mount servers even if they are not connected."""
        mock_supervisor = MagicMock()
        mock_supervisor.get_bridge.return_value = None

        mock_registry = MagicMock()
        state = MagicMock()
        state.config.name = "offline-server"
        mock_registry.list_all.return_value = [state]

        MockProxy.return_value = MagicMock()

        build_mcp_gateway(mock_supervisor, mock_registry)

        # Proxy created even though server has no bridge
        assert MockProxy.call_count == 1

    @patch("router.servers.mcp_gateway.FastMCPProxy")
    def test_skips_server_on_proxy_error(self, MockProxy):
        """Gateway should skip a server if proxy creation fails."""
        MockProxy.side_effect = [RuntimeError("bad"), MagicMock()]

        mock_supervisor = MagicMock()
        mock_registry = MagicMock()

        states = []
        for name in ["bad-server", "good-server"]:
            state = MagicMock()
            state.config.name = name
            states.append(state)
        mock_registry.list_all.return_value = states

        # Should not raise — skips bad, mounts good
        gateway = build_mcp_gateway(mock_supervisor, mock_registry)
        assert MockProxy.call_count == 2

    @patch("router.servers.mcp_gateway.FastMCPProxy")
    def test_factory_receives_correct_server_name(self, MockProxy):
        """Each proxy's factory should be bound to the correct server name."""
        mock_supervisor = MagicMock()

        # Two bridges with distinct clients
        bridge_a = MagicMock()
        bridge_a.is_connected = True
        bridge_a.client = MagicMock(name="client-a")

        bridge_b = MagicMock()
        bridge_b.is_connected = True
        bridge_b.client = MagicMock(name="client-b")

        def get_bridge(name):
            return {"server-a": bridge_a, "server-b": bridge_b}.get(name)

        mock_supervisor.get_bridge.side_effect = get_bridge

        mock_registry = MagicMock()
        states = []
        for name in ["server-a", "server-b"]:
            state = MagicMock()
            state.config.name = name
            states.append(state)
        mock_registry.list_all.return_value = states

        MockProxy.return_value = MagicMock()

        build_mcp_gateway(mock_supervisor, mock_registry)

        # Extract the factories passed to FastMCPProxy
        factories = [call.kwargs["client_factory"] for call in MockProxy.call_args_list]

        assert factories[0]() is bridge_a.client
        assert factories[1]() is bridge_b.client
