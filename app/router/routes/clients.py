"""Client profile endpoints (tool + model profiles).

These endpoints expose read-only derived configuration for a given client,
based on `app/configs/enhancement-rules.json`.

Design goals:
- Keep `tool_profile` and `model_profile` separate (can be combined later).
- Centralize defaulting/merging logic so dashboards and bridges don't drift.
- Avoid write/PATCH endpoints until we have a clear source-of-truth policy.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from router.config.settings import get_settings

logger = logging.getLogger(__name__)


class ToolProfileResponse(BaseModel):
    client: str
    disclosure: str = Field(default="full", description="full|progressive")
    tier1_servers: list[str] = Field(default_factory=list)
    source: str = Field(default="default", description="default|client_override")


class ModelProfileResponse(BaseModel):
    client: str
    model_profile: str | None = None
    resolved_model: str
    source: str = Field(default="default", description="default|client_override")


def _rules_path() -> Path:
    settings = get_settings()
    return Path(settings.workspace_root) / "app" / settings.enhancement_rules_config


def _load_rules(path: Path | None = None) -> dict[str, Any]:
    path = path or _rules_path()
    if not path.exists():
        raise HTTPException(503, f"Enhancement rules not found: {path}")
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.warning("Failed to parse enhancement rules: %s", e)
        raise HTTPException(503, "Enhancement rules invalid JSON")


def _merged_client_rule(rules: dict[str, Any], client: str) -> dict[str, Any]:
    default_rule = rules.get("default", {}) if isinstance(rules.get("default"), dict) else {}
    clients = rules.get("clients", {}) if isinstance(rules.get("clients"), dict) else {}
    override = clients.get(client, {}) if isinstance(clients.get(client), dict) else {}
    return {**default_rule, **override}


def create_clients_router(rules_path: Path | None = None) -> APIRouter:
    router = APIRouter(tags=["clients"])

    @router.get("/clients/{name}/tool-profile", response_model=ToolProfileResponse)
    async def get_tool_profile(name: str) -> ToolProfileResponse:
        rules = _load_rules(rules_path)
        merged = _merged_client_rule(rules, name)

        tp = merged.get("tool_profile") if isinstance(merged.get("tool_profile"), dict) else None
        if not tp:
            return ToolProfileResponse(client=name, disclosure="full", tier1_servers=[], source="default")

        disclosure = tp.get("disclosure", "full")
        tier1 = tp.get("tier1_servers", [])
        if not isinstance(tier1, list):
            tier1 = []
        tier1 = [str(s) for s in tier1 if s]

        return ToolProfileResponse(
            client=name,
            disclosure=str(disclosure),
            tier1_servers=tier1,
            source="client_override",
        )

    @router.get("/clients/{name}/model-profile", response_model=ModelProfileResponse)
    async def get_model_profile(name: str) -> ModelProfileResponse:
        rules = _load_rules(rules_path)
        merged = _merged_client_rule(rules, name)

        profiles = rules.get("model_profiles", {}) if isinstance(rules.get("model_profiles"), dict) else {}
        requested = merged.get("model_profile")
        base_model = merged.get("model") or rules.get("default", {}).get("model") or "unknown"

        if requested and isinstance(requested, str) and requested in profiles:
            info = profiles.get(requested, {})
            resolved = info.get("model") if isinstance(info, dict) else None
            if resolved:
                return ModelProfileResponse(
                    client=name,
                    model_profile=requested,
                    resolved_model=str(resolved),
                    source="client_override",
                )

        # No valid profile mapping — fall back to the merged "model" field.
        return ModelProfileResponse(
            client=name,
            model_profile=str(requested) if isinstance(requested, str) else None,
            resolved_model=str(base_model),
            source="default" if requested is None else "client_override",
        )

    return router
