"""
Pytest configuration and shared fixtures for AgentHub tests.

Provides common test utilities, mocks, and fixtures used across all test modules.
"""

import pytest
from pathlib import Path
import tempfile
import json


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test configuration files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_mcp_servers_config():
    """Sample MCP servers configuration for testing."""
    return {
        "servers": {
            "test-server": {
                "package": "@test/server",
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@test/server"],
                "env": {},
                "auto_start": False,
                "restart_on_failure": True,
                "max_restarts": 3,
                "health_check_interval": 30,
                "description": "Test server for unit tests"
            },
            "http-server": {
                "package": "@test/http-server",
                "transport": "http",
                "url": "http://localhost:8080",
                "auto_start": False,
                "description": "HTTP test server"
            }
        }
    }


@pytest.fixture
def sample_enhancement_rules():
    """Sample enhancement rules configuration for testing."""
    return {
        "default": {
            "enabled": True,
            "model": "llama3.2:3b",
            "system_prompt": "Improve clarity. Return only enhanced prompt."
        },
        "clients": {
            "test-client": {
                "model": "test-model",
                "system_prompt": "Test system prompt."
            }
        },
        "fallback_chain": ["phi3:mini", None]
    }


@pytest.fixture
def mock_config_files(temp_config_dir, sample_mcp_servers_config, sample_enhancement_rules):
    """Create temporary configuration files for testing."""
    servers_file = temp_config_dir / "mcp-servers.json"
    enhancement_file = temp_config_dir / "enhancement-rules.json"

    servers_file.write_text(json.dumps(sample_mcp_servers_config, indent=2))
    enhancement_file.write_text(json.dumps(sample_enhancement_rules, indent=2))

    return {
        "servers": servers_file,
        "enhancement": enhancement_file
    }
