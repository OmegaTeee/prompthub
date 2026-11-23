"""Live integration checks for the configured local LLM provider."""

import json
import os
from pathlib import Path

import httpx
import pytest

from router.config.settings import get_settings
from router.enhancement.llm_client import LLMClient, LLMConfig

ROUTER_URL = os.environ["PROMPTHUB_TEST_URL"]
APP_DIR = Path(__file__).resolve().parents[2]


def _default_rule_model(settings) -> str:
    """Model the router uses for an unconfigured client: the rules file's default."""
    rules_path = Path(settings.enhancement_rules_config)
    if not rules_path.is_absolute():
        rules_path = APP_DIR / rules_path
    rules = json.loads(rules_path.read_text())
    return rules.get("default", {}).get("model") or settings.llm_model


@pytest.mark.asyncio
@pytest.mark.requires_llm
async def test_enhancement_uses_configured_local_provider(live_router):
    """The router sends enhancement requests to the configured local model."""
    settings = get_settings()
    prompt = "Summarize how a local model endpoint is configured."
    timeout = float(settings.llm_timeout) + 10
    endpoint = f"{settings.llm_host}:{settings.llm_port}"
    headers = (
        {"Authorization": f"Bearer {settings.llm_api_key}"}
        if settings.llm_api_key
        else {}
    )
    local_llm = LLMClient(
        LLMConfig(
            base_url=f"http://{endpoint}/v1",
            timeout=timeout,
            extra_headers=headers,
        )
    )
    try:
        has_orchestrator_model = await local_llm.has_model(
            settings.llm_orchestrator_model
        )
    finally:
        await local_llm.close()

    assert has_orchestrator_model, (
        f"Configured local provider {endpoint} does not expose orchestrator model "
        f"{settings.llm_orchestrator_model}"
    )

    async with httpx.AsyncClient(base_url=ROUTER_URL, timeout=timeout) as client:
        response = await client.post(
            "/llm/enhance",
            headers={"X-Client-Name": "pytest-local-provider"},
            json={"prompt": prompt, "bypass_cache": True},
        )
        cached_response = await client.post(
            "/llm/enhance",
            headers={"X-Client-Name": "pytest-local-provider"},
            json={"prompt": prompt},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["original"] == prompt
    assert data["model"] == _default_rule_model(settings)
    assert data["provider"] == "llm", (
        f"Configured local provider {endpoint} failed: {data.get('error')}"
    )
    assert data["error"] is None, (
        f"Configured local provider {endpoint} failed: {data['error']}"
    )

    assert cached_response.status_code == 200, cached_response.text
    cached_data = cached_response.json()
    assert cached_data["cached"] is True
    assert cached_data["enhanced"] == data["enhanced"]
