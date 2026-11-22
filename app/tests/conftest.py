"""
Pytest configuration and shared fixtures for PromptHub tests.

Provides common test utilities, mocks, and fixtures used across all test modules.
"""

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest

# --- Isolated router for live integration tests ----------------------------
# Tests that need a running router read PROMPTHUB_TEST_URL and request the
# ``live_router`` fixture. By default the fixture starts a private router on a
# free port with a throwaway DATA_DIR, so tests never touch the daemon on
# :9090 (they stop and start MCP servers). Set PROMPTHUB_TEST_URL yourself to
# point the tests at an already-running instance instead.
APP_DIR = Path(__file__).resolve().parent.parent
_SPAWN_ROUTER = "PROMPTHUB_TEST_URL" not in os.environ
if _SPAWN_ROUTER:
    with socket.socket() as _s:
        _s.bind(("127.0.0.1", 0))
        _TEST_PORT = _s.getsockname()[1]
    os.environ["PROMPTHUB_TEST_URL"] = f"http://127.0.0.1:{_TEST_PORT}"
ROUTER_URL = os.environ["PROMPTHUB_TEST_URL"]
ROUTER_STARTUP_TIMEOUT = 90  # seconds; auto-start MCP servers spawn at boot


_ALLOWED_NETLOC = httpx.URL(ROUTER_URL).netloc


@pytest.fixture(autouse=True)
def block_real_http(request, monkeypatch):
    """Fail any test whose code sends a real HTTP request, except to the test router.

    Only ``httpx.HTTPTransport``/``AsyncHTTPTransport`` are patched; in-process
    transports (FastAPI ``TestClient``, ``ASGITransport``) never hit the network
    and are unaffected. A blocked request raises ``httpx.ConnectError`` so the
    code under test sees an ordinary offline failure, and the test is failed at
    teardown even if that error was swallowed (e.g. turned into a 502).
    Tests marked ``requires_llm`` may reach the local LLM server. Tests marked
    ``offline`` still get the ``ConnectError`` but are not failed, because
    exercising the unreachable-server path is their purpose.
    """
    if request.node.get_closest_marker("requires_llm"):
        yield
        return
    offline_expected = request.node.get_closest_marker("offline") is not None

    blocked: list[str] = []

    def _check(req: httpx.Request) -> None:
        if req.url.netloc != _ALLOWED_NETLOC:
            blocked.append(f"{req.method} {req.url}")
            raise httpx.ConnectError(
                f"real HTTP blocked in tests: {req.method} {req.url}", request=req
            )

    sync_send = httpx.HTTPTransport.handle_request
    async_send = httpx.AsyncHTTPTransport.handle_async_request

    def guarded_sync(self, req):
        _check(req)
        return sync_send(self, req)

    async def guarded_async(self, req):
        _check(req)
        return await async_send(self, req)

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", guarded_sync)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", guarded_async)
    yield
    if blocked and not offline_expected:
        pytest.fail(
            "Test sent real HTTP requests; mock them or mark the test requires_llm:\n  "
            + "\n  ".join(blocked),
            pytrace=False,
        )


@pytest.fixture(scope="session")
def live_router(tmp_path_factory):
    """Yield the URL of a router the tests may freely mutate."""
    if not _SPAWN_ROUTER:
        yield ROUTER_URL
        return

    data_dir = tmp_path_factory.mktemp("prompthub-data")
    log_path = data_dir / "router.log"
    env = {
        **os.environ,
        "HOST": "127.0.0.1",
        "PORT": str(_TEST_PORT),
        "DATA_DIR": str(data_dir),
    }
    with open(log_path, "wb") as log:
        # Own process group, so teardown also kills the MCP servers it spawns.
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "router.main:app",
             "--host", "127.0.0.1", "--port", str(_TEST_PORT)],
            cwd=APP_DIR, env=env, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    try:
        deadline = time.monotonic() + ROUTER_STARTUP_TIMEOUT
        while True:
            if proc.poll() is not None:
                pytest.fail(f"Test router exited early; log:\n{log_path.read_text()[-3000:]}")
            try:
                if httpx.get(f"{ROUTER_URL}/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if time.monotonic() > deadline:
                pytest.fail(f"Test router not healthy after {ROUTER_STARTUP_TIMEOUT}s; log:\n"
                            f"{log_path.read_text()[-3000:]}")
            time.sleep(1)
        yield ROUTER_URL
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=20)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)


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
