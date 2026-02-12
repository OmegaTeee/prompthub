from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from router.middleware.enhancement import EnhancementMiddleware


class DummyEnhancer:
    async def enhance(self, prompt: str, client_name: str | None = None, bypass_cache: bool = False):
        # Return a simple object with .enhanced attribute to match real service
        return SimpleNamespace(enhanced=prompt + "[ENHANCED]")


def _create_app_with_enhancer(enhancer):
    app = FastAPI()
    # attach service to app.state for middleware to pick up
    app.state.enhancement_service = enhancer
    app.add_middleware(EnhancementMiddleware)

    @app.post("/mcp/echo")
    async def echo(request: Request):
        return await request.json()

    return app


def test_integration_body_replacement_simple():
    app = _create_app_with_enhancer(DummyEnhancer())
    client = TestClient(app)

    body = {"jsonrpc": "2.0", "method": "tools.call", "params": {"prompt": "hello"}}
    r = client.post("/mcp/echo", json=body, headers={"X-Enhance": "true"})
    assert r.status_code == 200
    data = r.json()
    assert data["params"]["prompt"].endswith("[ENHANCED]")


def test_integration_body_replacement_nested_arguments():
    app = _create_app_with_enhancer(DummyEnhancer())
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
