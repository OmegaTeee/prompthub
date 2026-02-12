import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import router.main as main_mod
from router.enhancement.service import EnhancementResult
from router.middleware.enhancement import EnhancementMiddleware


class DummyEnhancer:
    async def enhance(self, prompt, client_name=None, bypass_cache=False):
        return EnhancementResult(original=prompt, enhanced=prompt + " [ENHANCED]", model="test")


class FailingEnhancer:
    """Enhancement service that raises exceptions."""

    async def enhance(self, prompt, client_name=None, bypass_cache=False):
        raise ValueError("Enhancement failed")


def test_enhancement_middleware_header_opt_in(monkeypatch):
    # Patch global enhancement_service reference used by middleware
    monkeypatch.setattr(main_mod, "enhancement_service", DummyEnhancer())
    # Ensure settings allow enhancement or header is respected
    class _S:
        auto_enhance_mcp = True
        max_enhancement_body_size = 10 * 1024 * 1024

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    # Sanity: enhancement_service should be available on router.main
    assert getattr(main_mod, "enhancement_service", None) is not None

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app)

    body = {"jsonrpc": "2.0", "method": "tools.call", "params": {"prompt": "hello"}}
    r = client.post("/mcp/echo", json=body, headers={"X-Enhance": "true"})

    assert r.status_code == 200
    data = r.json()
    assert data["params"]["prompt"].endswith("[ENHANCED]")


def test_enhancement_middleware_no_header_no_change(monkeypatch):
    monkeypatch.setattr(main_mod, "enhancement_service", DummyEnhancer())
    class _S:
        auto_enhance_mcp = False
        max_enhancement_body_size = 10 * 1024 * 1024

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app)

    body = {"jsonrpc": "2.0", "method": "tools.call", "params": {"prompt": "nochange"}}
    r = client.post("/mcp/echo", json=body)

    assert r.status_code == 200
    data = r.json()
    assert data["params"]["prompt"] == "nochange"


def test_enhancement_middleware_nested_arguments(monkeypatch):
    """Test enhancement of params.arguments.prompt structure."""
    monkeypatch.setattr(main_mod, "enhancement_service", DummyEnhancer())

    class _S:
        auto_enhance_mcp = True
        max_enhancement_body_size = 10 * 1024 * 1024

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app)

    body = {
        "jsonrpc": "2.0",
        "method": "tools.call",
        "params": {"arguments": {"prompt": "nested prompt"}},
    }
    r = client.post("/mcp/echo", json=body, headers={"X-Enhance": "true"})

    assert r.status_code == 200
    data = r.json()
    assert data["params"]["arguments"]["prompt"].endswith("[ENHANCED]")


def test_enhancement_middleware_service_unavailable(monkeypatch):
    """Test graceful degradation when enhancement service is None."""
    monkeypatch.setattr(main_mod, "enhancement_service", None)

    class _S:
        auto_enhance_mcp = True
        max_enhancement_body_size = 10 * 1024 * 1024

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app)

    body = {"jsonrpc": "2.0", "params": {"prompt": "test"}}
    r = client.post("/mcp/echo", json=body, headers={"X-Enhance": "true"})

    # Should pass through without enhancement
    assert r.status_code == 200
    assert r.json()["params"]["prompt"] == "test"


def test_enhancement_middleware_service_exception(monkeypatch):
    """Test graceful error handling when enhancement service raises."""
    monkeypatch.setattr(main_mod, "enhancement_service", FailingEnhancer())

    class _S:
        auto_enhance_mcp = True
        max_enhancement_body_size = 10 * 1024 * 1024

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app)

    body = {"jsonrpc": "2.0", "params": {"prompt": "test"}}
    r = client.post("/mcp/echo", json=body, headers={"X-Enhance": "true"})

    # Should pass through on error
    assert r.status_code == 200
    assert r.json()["params"]["prompt"] == "test"


def test_enhancement_middleware_invalid_json(monkeypatch):
    """Test handling of malformed JSON bodies."""
    monkeypatch.setattr(main_mod, "enhancement_service", DummyEnhancer())

    class _S:
        auto_enhance_mcp = True
        max_enhancement_body_size = 10 * 1024 * 1024

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        body = await request.body()
        return {"received": body.decode("utf-8")}

    client = TestClient(app)

    r = client.post(
        "/mcp/echo",
        content=b"{invalid json}",
        headers={"X-Enhance": "true", "Content-Type": "application/json"},
    )

    # Should pass through invalid JSON without crashing
    assert r.status_code == 200


@pytest.mark.parametrize("header_value", ["1", "true", "True", "yes", "YES", "on", "ON"])
def test_enhancement_middleware_header_variations(header_value, monkeypatch):
    """Test all supported X-Enhance header values."""
    monkeypatch.setattr(main_mod, "enhancement_service", DummyEnhancer())

    class _S:
        auto_enhance_mcp = False  # Only header should trigger
        max_enhancement_body_size = 10 * 1024 * 1024

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app)

    body = {"jsonrpc": "2.0", "params": {"prompt": "test"}}
    r = client.post("/mcp/echo", json=body, headers={"X-Enhance": header_value})

    assert r.status_code == 200
    assert r.json()["params"]["prompt"].endswith("[ENHANCED]")


def test_enhancement_middleware_large_body_rejected(monkeypatch):
    """Test that overly large request bodies are rejected."""
    monkeypatch.setattr(main_mod, "enhancement_service", DummyEnhancer())

    class _S:
        auto_enhance_mcp = True
        max_enhancement_body_size = 100  # Very small limit for testing

    monkeypatch.setattr("router.middleware.enhancement.get_settings", lambda: _S())

    app = FastAPI()
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app)

    body = {"jsonrpc": "2.0", "params": {"prompt": "test"}}
    # Simulate large content-length header
    r = client.post(
        "/mcp/echo", json=body, headers={"X-Enhance": "true", "Content-Length": "1000000"}
    )

    # Should pass through without enhancement (body too large)
    assert r.status_code == 200
    # Body should not be enhanced (too large)
    assert r.json()["params"]["prompt"] == "test"
