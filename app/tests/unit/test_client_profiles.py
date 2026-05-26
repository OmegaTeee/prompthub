import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from router.enhancement.service import EnhancementService
from router.routes.clients import create_clients_router


def test_clients_tool_profile_endpoint_defaults_and_overrides(tmp_path):
    rules_path = tmp_path / "enhancement-rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "default": {"enabled": True, "model": "base"},
                "clients": {
                    "vscode": {
                        "tool_profile": {
                            "disclosure": "progressive",
                            "tier1_servers": ["memory"],
                        }
                    }
                },
            }
        )
    )

    app = FastAPI()
    app.include_router(create_clients_router(rules_path=rules_path))
    client = TestClient(app)

    r = client.get("/clients/unknown/tool-profile")
    assert r.status_code == 200
    assert r.json()["disclosure"] == "full"
    assert r.json()["tier1_servers"] == []
    assert r.json()["source"] == "default"

    r2 = client.get("/clients/vscode/tool-profile")
    assert r2.status_code == 200
    assert r2.json()["disclosure"] == "progressive"
    assert r2.json()["tier1_servers"] == ["memory"]
    assert r2.json()["source"] == "client_override"


@pytest.mark.asyncio
async def test_enhancement_service_model_profile_resolution(tmp_path):
    rules_path = tmp_path / "enhancement-rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "default": {"enabled": True, "model": "daemon"},
                "model_profiles": {"coder": {"model": "coder-model"}},
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
    assert rule.model == "coder-model"

