"""HTTP tests for router.routes.clients.

Exercises the /clients/{name}/tool-profile endpoint through FastAPI's
TestClient with an injected rules_path, so tests run hermetically against
a tmp_path-backed enhancement-rules.json.

What is covered:
- Default response when the client has no `tool_profile` entry.
- Client_override response when `tool_profile` is set.
- Malformed `tool_profile` (wrong shape) degrades gracefully to defaults.
- Missing `tier1_servers` list is treated as empty.

Bridge-side fallback (fetchToolProfileFromRouter) is exercised by manual
verification in the PR test plan — pytest doesn't run the JS bridge.
"""

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from router.routes.clients import create_clients_router


def _make_client(tmp_path, rules_dict):
    rules_path = tmp_path / "enhancement-rules.json"
    rules_path.write_text(json.dumps(rules_dict))
    app = FastAPI()
    app.include_router(create_clients_router(rules_path=rules_path))
    return TestClient(app)


def test_tool_profile_defaults_when_client_unknown(tmp_path):
    """Unknown client → safe default: full disclosure, no tier-1 servers."""
    client = _make_client(
        tmp_path,
        {
            "default": {"enabled": True, "model": "x"},
            "clients": {},
        },
    )
    r = client.get("/clients/anything/tool-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["client"] == "anything"
    assert body["disclosure"] == "full"
    assert body["tier1_servers"] == []
    assert body["source"] == "default"


def test_tool_profile_returns_client_override(tmp_path):
    """Client with tool_profile → progressive + tier1 surface verbatim."""
    client = _make_client(
        tmp_path,
        {
            "default": {"enabled": True, "model": "x"},
            "clients": {
                "vscode": {
                    "tool_profile": {
                        "disclosure": "progressive",
                        "tier1_servers": ["desktop-commander", "context7", "memory"],
                    }
                }
            },
        },
    )
    r = client.get("/clients/vscode/tool-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["disclosure"] == "progressive"
    assert body["tier1_servers"] == ["desktop-commander", "context7", "memory"]
    assert body["source"] == "client_override"


def test_tool_profile_drops_empty_and_coerces_strings(tmp_path):
    """tier1_servers entries are coerced to strings; empty/falsy entries are dropped."""
    client = _make_client(
        tmp_path,
        {
            "default": {},
            "clients": {
                "weird": {
                    "tool_profile": {
                        "disclosure": "progressive",
                        # Mixed types simulate hand-edited config drift.
                        "tier1_servers": ["memory", "", None, 42, "context7"],
                    }
                }
            },
        },
    )
    r = client.get("/clients/weird/tool-profile")
    assert r.status_code == 200
    body = r.json()
    # 42 coerces to "42"; empty and None are dropped.
    assert body["tier1_servers"] == ["memory", "42", "context7"]


def test_tool_profile_malformed_block_falls_back_to_default(tmp_path):
    """A non-dict `tool_profile` value should not 500 — return defaults."""
    client = _make_client(
        tmp_path,
        {
            "default": {},
            "clients": {
                "broken": {"tool_profile": "not-a-dict"}
            },
        },
    )
    r = client.get("/clients/broken/tool-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["disclosure"] == "full"
    assert body["tier1_servers"] == []
    assert body["source"] == "default"


def test_tool_profile_missing_tier1_list_is_empty(tmp_path):
    """tool_profile with only `disclosure` set → empty tier1 list."""
    client = _make_client(
        tmp_path,
        {
            "default": {},
            "clients": {
                "minimal": {"tool_profile": {"disclosure": "progressive"}}
            },
        },
    )
    r = client.get("/clients/minimal/tool-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["disclosure"] == "progressive"
    assert body["tier1_servers"] == []
    assert body["source"] == "client_override"
