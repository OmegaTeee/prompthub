"""HTTP tests for router.routes.clients.

Exercises both `/clients/{name}/tool-profile` and
`/clients/{name}/model-profile` through FastAPI's TestClient with an
injected rules_path, so tests run hermetically against a tmp_path-backed
enhancement-rules.json.

What is covered:
- Tool profile: default, override, malformed shape, missing tier1, coercion.
- Model profile: default (no opt-in), client_override (profile resolved),
  profile_missing (typo'd profile name surfaces as distinct source),
  explicit `model` override without profile.
- Service-level: EnhancementService resolves model via model_profile during
  rule load (this is what the bridge and the dashboard observe).

Bridge-side fallback (fetchToolProfileFromRouter) is exercised by manual
verification in the PR test plan — pytest doesn't run the JS bridge.
"""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from router.enhancement.service import EnhancementService
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


# Normalization + 503 paths (Copilot review follow-up)
# ---------------------------------------------------------------------------


def test_tool_profile_disclosure_is_case_normalized(tmp_path):
    """`Progressive` and surrounding whitespace should normalize to `progressive`."""
    client = _make_client(
        tmp_path,
        {
            "default": {},
            "clients": {
                "wonky": {
                    "tool_profile": {
                        "disclosure": "  Progressive  ",
                        "tier1_servers": [" memory ", "context7"],
                    }
                }
            },
        },
    )
    r = client.get("/clients/wonky/tool-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["disclosure"] == "progressive"
    # tier1 entries are also whitespace-stripped.
    assert body["tier1_servers"] == ["memory", "context7"]


def test_tool_profile_disclosure_clamps_to_full_on_invalid(tmp_path):
    """An unknown disclosure value (`bogus`) falls back to `full`."""
    client = _make_client(
        tmp_path,
        {
            "default": {},
            "clients": {
                "wat": {"tool_profile": {"disclosure": "bogus"}}
            },
        },
    )
    r = client.get("/clients/wat/tool-profile")
    assert r.status_code == 200
    assert r.json()["disclosure"] == "full"


def test_tool_profile_returns_503_on_non_object_root(tmp_path):
    """A syntactically valid but wrong-shape config (top-level array) → 503."""
    rules_path = tmp_path / "enhancement-rules.json"
    rules_path.write_text(json.dumps(["not", "a", "dict"]))
    app = FastAPI()
    app.include_router(create_clients_router(rules_path=rules_path))
    c = TestClient(app)
    r = c.get("/clients/whatever/tool-profile")
    # Was previously 500 from a downstream .get() on a list.
    assert r.status_code == 503


# ---------------------------------------------------------------------------
# /clients/{name}/model-profile
# ---------------------------------------------------------------------------


def test_model_profile_default_when_no_opt_in(tmp_path):
    """Unknown client + no profile reference → resolves to default model."""
    client = _make_client(
        tmp_path,
        {
            "default": {"model": "qwen3-4b-instruct-2507"},
            "model_profiles": {"coder": {"model": "coder-model"}},
            "clients": {},
        },
    )
    r = client.get("/clients/anything/model-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["model_profile"] is None
    assert body["resolved_model"] == "qwen3-4b-instruct-2507"
    assert body["source"] == "default"


def test_model_profile_resolves_to_profile_when_set(tmp_path):
    """Client with valid model_profile → resolved_model comes from profile."""
    client = _make_client(
        tmp_path,
        {
            "default": {"model": "qwen3-4b-instruct-2507"},
            "model_profiles": {
                "coder": {"model": "Qwopus3.5-9B-Coder-GGUF"}
            },
            "clients": {
                "vscode": {
                    "model": "qwen3-1.7b",
                    "model_profile": "coder",
                }
            },
        },
    )
    r = client.get("/clients/vscode/model-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["model_profile"] == "coder"
    # Profile wins over the explicit `model` field on the rule.
    assert body["resolved_model"] == "Qwopus3.5-9B-Coder-GGUF"
    assert body["source"] == "client_override"


def test_model_profile_missing_surfaces_distinct_source(tmp_path):
    """Typo'd profile name → resolved falls back, source=profile_missing."""
    client = _make_client(
        tmp_path,
        {
            "default": {"model": "qwen3-4b-instruct-2507"},
            "model_profiles": {"coder": {"model": "Qwopus3.5-9B-Coder-GGUF"}},
            "clients": {
                "vscode": {
                    "model": "qwen3-1.7b",
                    "model_profile": "codeer",  # typo
                }
            },
        },
    )
    r = client.get("/clients/vscode/model-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["model_profile"] == "codeer"
    # Falls back to the client's explicit `model` field.
    assert body["resolved_model"] == "qwen3-1.7b"
    assert body["source"] == "profile_missing"


def test_model_profile_explicit_model_without_profile(tmp_path):
    """No profile reference but client overrides `model` → source=client_override."""
    client = _make_client(
        tmp_path,
        {
            "default": {"model": "qwen3-4b-instruct-2507"},
            "model_profiles": {},
            "clients": {
                "comfyui": {"model": "stable-diffusion-prompt"}
            },
        },
    )
    r = client.get("/clients/comfyui/model-profile")
    assert r.status_code == 200
    body = r.json()
    assert body["model_profile"] is None
    assert body["resolved_model"] == "stable-diffusion-prompt"
    assert body["source"] == "client_override"


# ---------------------------------------------------------------------------
# EnhancementService resolution (mirrors what the bridge actually observes)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enhancement_service_resolves_model_via_profile(tmp_path):
    """Service-level: get_rule(client).model reflects profile resolution."""
    rules_path = tmp_path / "enhancement-rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "default": {
                    "enabled": True,
                    "model": "qwen3-4b-instruct-2507",
                },
                "model_profiles": {
                    "coder": {"model": "Qwopus3.5-9B-Coder-GGUF"}
                },
                "clients": {
                    "vscode": {
                        "model_profile": "coder",
                        "system_prompt": "x",
                    }
                },
            }
        )
    )

    svc = EnhancementService(rules_path=rules_path, cache_persistent=False)
    await svc.initialize()

    rule = svc.get_rule("vscode")
    assert rule.model == "Qwopus3.5-9B-Coder-GGUF"

    # Sanity: clients without profile still see the default model.
    default_rule = svc.get_rule("default")
    assert default_rule.model == "qwen3-4b-instruct-2507"
