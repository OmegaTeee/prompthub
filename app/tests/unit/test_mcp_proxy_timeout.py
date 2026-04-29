"""
Unit tests for per-server proxy_timeout resolution in mcp_proxy.

The proxy picks a bridge timeout per request:
- Use ServerConfig.proxy_timeout when set on the server config
- Fall back to DEFAULT_BRIDGE_TIMEOUT otherwise

These tests drive the route through the FastAPI test client with all
backing services mocked, asserting that bridge.send() receives the
expected timeout value.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from router.routes.mcp_proxy import DEFAULT_BRIDGE_TIMEOUT, create_mcp_proxy_router
from router.servers.models import (
    ProcessInfo,
    ServerConfig,
    ServerStatus,
    ServerTransport,
)


def _make_config(name: str, *, proxy_timeout: float | None = None) -> ServerConfig:
    return ServerConfig(
        name=name,
        package=f"@test/{name}",
        transport=ServerTransport.STDIO,
        command="node",
        args=["server.js"],
        auto_start=True,
        proxy_timeout=proxy_timeout,
    )


def _build_app(config: ServerConfig, bridge_send: AsyncMock) -> FastAPI:
    """Build a FastAPI app wired with mocks for registry/supervisor/breakers."""
    registry = MagicMock()
    registry.get.return_value = config
    registry.get_process_info.return_value = ProcessInfo(status=ServerStatus.RUNNING)

    bridge = MagicMock()
    bridge.send = bridge_send

    supervisor = MagicMock()
    supervisor.get_bridge.return_value = bridge
    supervisor.start_server = AsyncMock()

    breaker = MagicMock()
    breaker.check = MagicMock()
    breaker.record_success = MagicMock()
    breaker.record_failure = MagicMock()
    breakers = MagicMock()
    breakers.get.return_value = breaker

    router = create_mcp_proxy_router(
        get_registry=lambda: registry,
        get_supervisor=lambda: supervisor,
        get_circuit_breakers=lambda: breakers,
    )

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_proxy_uses_default_timeout_when_config_has_no_override() -> None:
    """Servers without proxy_timeout fall back to DEFAULT_BRIDGE_TIMEOUT."""
    config = _make_config("context7", proxy_timeout=None)
    bridge_send = AsyncMock(return_value={"jsonrpc": "2.0", "result": {}, "id": 1})
    app = _build_app(config, bridge_send)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/mcp/context7/tools/call",
            json={"jsonrpc": "2.0", "method": "tools/call", "id": 1},
        )

    assert resp.status_code == 200
    assert bridge_send.await_count == 1
    assert bridge_send.await_args.kwargs["timeout"] == DEFAULT_BRIDGE_TIMEOUT
    assert resp.json()["metadata"]["timeout_used"] == DEFAULT_BRIDGE_TIMEOUT


@pytest.mark.asyncio
async def test_proxy_uses_per_server_proxy_timeout_when_set() -> None:
    """Servers with proxy_timeout=180 pass 180.0 into bridge.send()."""
    config = _make_config("perplexity-comet", proxy_timeout=180)
    bridge_send = AsyncMock(return_value={"jsonrpc": "2.0", "result": {}, "id": 1})
    app = _build_app(config, bridge_send)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/mcp/perplexity-comet/tools/call",
            json={"jsonrpc": "2.0", "method": "tools/call", "id": 1},
        )

    assert resp.status_code == 200
    assert bridge_send.await_count == 1
    assert bridge_send.await_args.kwargs["timeout"] == 180.0
    # Echoed back in response metadata for dashboard/debug visibility.
    assert resp.json()["metadata"]["timeout_used"] == 180.0


@pytest.mark.asyncio
async def test_proxy_timeout_field_accepts_float() -> None:
    """proxy_timeout is declared as float | None and accepts fractional values."""
    config = _make_config("slow-server", proxy_timeout=45.5)
    bridge_send = AsyncMock(return_value={"jsonrpc": "2.0", "result": {}, "id": 1})
    app = _build_app(config, bridge_send)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/mcp/slow-server/tools/call",
            json={"jsonrpc": "2.0", "method": "tools/call", "id": 1},
        )

    assert resp.status_code == 200
    assert bridge_send.await_args.kwargs["timeout"] == 45.5


@pytest.mark.parametrize("bad_value", [0, 0.0, -1, -30.5])
def test_proxy_timeout_rejects_non_positive_values(bad_value: float) -> None:
    """A misconfigured proxy_timeout fails fast at config-load, not at request time."""
    with pytest.raises(ValidationError):
        _make_config("misconfigured", proxy_timeout=bad_value)
