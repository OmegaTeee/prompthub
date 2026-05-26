"""Client profile endpoints — read-only derived configuration per client.

Currently exposes `GET /clients/{name}/tool-profile` only. A model-profile
endpoint lands in a follow-up PR with the model_profiles mechanism.

Design goals:
- Keep tool_profile and model_profile decoupled (they can be combined later
  on the client side if useful).
- Centralize the default-vs-override merging logic so the bridge and the
  dashboard cannot drift from `app/configs/enhancement-rules.json`.
- Read-only. No PATCH/POST until there is a clear source-of-truth policy
  (today the rules file is the source of truth; a write endpoint would
  need to settle conflicts with hand-edits).
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
    source: str = Field(
        default="default",
        description="default (no override in config) | client_override",
    )


def _rules_path() -> Path:
    """Resolve the active enhancement-rules.json path from settings."""
    settings = get_settings()
    return Path(settings.workspace_root) / "app" / settings.enhancement_rules_config


def _load_rules(path: Path | None = None) -> dict[str, Any]:
    """Read and parse enhancement-rules.json, raising 503 on missing/invalid."""
    path = path or _rules_path()
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"Enhancement rules not found: {path}")
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.warning("Failed to parse enhancement rules: %s", e)
        raise HTTPException(status_code=503, detail="Enhancement rules invalid JSON")


def _merged_client_rule(rules: dict[str, Any], client: str) -> dict[str, Any]:
    """Merge default rule with the named client's override (override wins)."""
    default_rule = rules.get("default", {})
    if not isinstance(default_rule, dict):
        default_rule = {}
    clients = rules.get("clients", {})
    if not isinstance(clients, dict):
        clients = {}
    override = clients.get(client, {})
    if not isinstance(override, dict):
        override = {}
    return {**default_rule, **override}


def create_clients_router(rules_path: Path | None = None) -> APIRouter:
    """Build the /clients sub-router. Pass rules_path for tests."""
    router = APIRouter(tags=["clients"])

    @router.get("/clients/{name}/tool-profile", response_model=ToolProfileResponse)
    async def get_tool_profile(name: str) -> ToolProfileResponse:
        rules = _load_rules(rules_path)
        merged = _merged_client_rule(rules, name)

        tp = merged.get("tool_profile")
        if not isinstance(tp, dict):
            # No tool_profile configured anywhere — safe default keeps
            # the bridge in `full` mode and the client unaware of the
            # progressive-disclosure mechanism.
            return ToolProfileResponse(
                client=name,
                disclosure="full",
                tier1_servers=[],
                source="default",
            )

        disclosure = tp.get("disclosure", "full")
        raw_tier1 = tp.get("tier1_servers", [])
        if not isinstance(raw_tier1, list):
            raw_tier1 = []
        # Coerce + filter so the bridge never has to defend against bad
        # config: drop empties, force-string everything else.
        tier1 = [str(s) for s in raw_tier1 if s]

        return ToolProfileResponse(
            client=name,
            disclosure=str(disclosure),
            tier1_servers=tier1,
            source="client_override",
        )

    return router
