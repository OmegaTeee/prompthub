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

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from router.config.settings import get_settings

logger = logging.getLogger(__name__)

_VALID_DISCLOSURE_MODES = frozenset({"full", "progressive"})


def _normalize_disclosure(raw: Any) -> str:
    """Lowercase, strip, and clamp `disclosure` to {full, progressive}.

    Invalid or unexpected values fall back to `full` — the same defensive
    posture the bridge takes for `TOOL_DISCLOSURE`. Centralized here so the
    endpoint, the dashboard, and any future consumer see consistent values.
    """
    value = str(raw).lower().strip() if raw is not None else ""
    return value if value in _VALID_DISCLOSURE_MODES else "full"


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


async def _load_rules(path: Path | None = None) -> dict[str, Any]:
    """Read and parse enhancement-rules.json, raising 503 on missing/invalid.

    Async + thread-pool file read for consistency with the rest of the
    service layer (EnhancementService uses asyncio.to_thread for the same
    file). Also validates that the top-level value is a JSON object — a
    valid-but-wrong-shape file (e.g., a top-level array) would otherwise
    surface as a 500 from a downstream `.get()` instead of a controlled 503.
    """
    path = path or _rules_path()
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"Enhancement rules not found: {path}")
    try:
        content = await asyncio.to_thread(path.read_text)
        data = json.loads(content)
    except Exception as e:
        logger.warning("Failed to parse enhancement rules: %s", e)
        raise HTTPException(status_code=503, detail="Enhancement rules invalid JSON")
    if not isinstance(data, dict):
        logger.warning(
            "Enhancement rules root is %s, expected object", type(data).__name__
        )
        raise HTTPException(
            status_code=503, detail="Enhancement rules root must be a JSON object"
        )
    return data


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
        rules = await _load_rules(rules_path)
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

        # Normalize disclosure once at the boundary so downstream consumers
        # (dashboard template, bridge) see a known-good lowercase value.
        # Hand-edited config with "Progressive" or "PROGRESSIVE" otherwise
        # silently falls through to `full` in the dashboard's exact-match
        # comparison.
        disclosure = _normalize_disclosure(tp.get("disclosure"))
        raw_tier1 = tp.get("tier1_servers", [])
        if not isinstance(raw_tier1, list):
            raw_tier1 = []
        # Coerce + trim + filter so the bridge never has to defend against
        # bad config: strip whitespace, drop empties, force-string everything
        # else. Matches the bridge's env-var parsing behavior.
        tier1 = [str(s).strip() for s in raw_tier1 if s]
        tier1 = [s for s in tier1 if s]

        return ToolProfileResponse(
            client=name,
            disclosure=disclosure,
            tier1_servers=tier1,
            source="client_override",
        )

    return router
