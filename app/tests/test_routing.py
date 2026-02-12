"""
Tests for server routing and registry.

Verifies:
- Server registry loads configurations correctly
- Server lookup by name works
- Unknown servers return appropriate errors
- Server CRUD operations
- Process state tracking
"""

import pytest
from pathlib import Path
from router.servers.registry import ServerRegistry
from router.servers.models import ServerConfig, ServerStatus, ServerTransport


class TestServerRegistry:
    """Test cases for server registry."""

    def test_load_empty_config(self, temp_config_dir):
        """Test loading with no config file creates empty registry."""
        config_file = temp_config_dir / "servers.json"
        registry = ServerRegistry(config_file)

        registry.load()

        assert len(registry.list_all()) == 0
        assert config_file.exists()

    def test_load_valid_config(self, mock_config_files):
        """Test loading valid server configuration."""
        registry = ServerRegistry(mock_config_files["servers"])

        registry.load()

        servers = registry.list_all()
        assert len(servers) == 2

        # Verify test-server loaded
        test_server = registry.get("test-server")
        assert test_server is not None
        assert test_server.name == "test-server"
        assert test_server.transport == ServerTransport.STDIO
        assert test_server.command == "npx"

    def test_get_existing_server(self, mock_config_files):
        """Test retrieving an existing server by name."""
        registry = ServerRegistry(mock_config_files["servers"])
        registry.load()

        server = registry.get("test-server")

        assert server is not None
        assert server.name == "test-server"
        assert server.package == "@test/server"

    def test_get_nonexistent_server(self, mock_config_files):
        """Test retrieving non-existent server returns None."""
        registry = ServerRegistry(mock_config_files["servers"])
        registry.load()

        server = registry.get("nonexistent")

        assert server is None

    def test_add_new_server(self, temp_config_dir):
        """Test adding a new server configuration."""
        config_file = temp_config_dir / "servers.json"
        registry = ServerRegistry(config_file)
        registry.load()

        new_server = ServerConfig(
            name="new-server",
            package="@new/server",
            transport=ServerTransport.STDIO,
            command="npx",
            args=["-y", "@new/server"]
        )

        registry.add(new_server)

        assert registry.get("new-server") is not None
        assert len(registry.list_all()) == 1

    def test_remove_server(self, mock_config_files):
        """Test removing a server configuration."""
        registry = ServerRegistry(mock_config_files["servers"])
        registry.load()

        initial_count = len(registry.list_all())
        registry.remove("test-server")

        assert registry.get("test-server") is None
        assert len(registry.list_all()) == initial_count - 1

    def test_list_all_returns_configs_and_processes(self, mock_config_files):
        """Test list_all returns both configs and process info."""
        registry = ServerRegistry(mock_config_files["servers"])
        registry.load()

        servers = registry.list_all()

        assert len(servers) == 2
        for server_state in servers:
            assert isinstance(server_state.config, ServerConfig)
            assert hasattr(server_state.process, "status")
            # Initial status should be STOPPED
            assert server_state.process.status == ServerStatus.STOPPED

    def test_save_and_reload_config(self, temp_config_dir):
        """Test saving and reloading configuration persists changes."""
        config_file = temp_config_dir / "servers.json"
        registry1 = ServerRegistry(config_file)
        registry1.load()

        # Add server and save
        server = ServerConfig(
            name="persistent-server",
            package="@test/persistent",
            transport=ServerTransport.HTTP,
            url="http://localhost:9000"
        )
        registry1.add(server)
        registry1.save()

        # Create new registry and load
        registry2 = ServerRegistry(config_file)
        registry2.load()

        loaded_server = registry2.get("persistent-server")
        assert loaded_server is not None
        assert loaded_server.name == "persistent-server"
        assert loaded_server.transport == ServerTransport.HTTP

    def test_process_state_tracking(self, mock_config_files):
        """Test process state is tracked separately from config."""
        registry = ServerRegistry(mock_config_files["servers"])
        registry.load()

        # Get process info
        process_info = registry.get_process_info("test-server")
        assert process_info is not None
        assert process_info.status == ServerStatus.STOPPED
        assert process_info.pid is None

        # Update process state
        registry.update_process_info("test-server", pid=12345, status=ServerStatus.RUNNING)

        updated_info = registry.get_process_info("test-server")
        assert updated_info.pid == 12345
        assert updated_info.status == ServerStatus.RUNNING

    def test_http_server_config_validation(self, mock_config_files):
        """Test HTTP server loads with URL instead of command."""
        registry = ServerRegistry(mock_config_files["servers"])
        registry.load()

        http_server = registry.get("http-server")
        assert http_server is not None
        assert http_server.transport == ServerTransport.HTTP
        assert http_server.url == "http://localhost:8080"
        assert http_server.command is None

    def test_auto_start_flag_preserved(self, mock_config_files):
        """Test auto_start flag is preserved during load."""
        registry = ServerRegistry(mock_config_files["servers"])
        registry.load()

        server = registry.get("test-server")
        assert server.auto_start is False

        http_server = registry.get("http-server")
        assert http_server.auto_start is False
