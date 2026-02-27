"""Prompt enhancement (Ollama) endpoints."""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from router.enhancement import PrivacyLevel

logger = logging.getLogger(__name__)


class EnhanceRequest(BaseModel):
    """Request body for prompt enhancement."""

    prompt: str
    bypass_cache: bool = False


def create_enhancement_router(
    get_enhancement_service: Callable[[], Any],
) -> APIRouter:
    router = APIRouter(tags=["enhancement"])

    @router.post("/ollama/enhance")
    async def enhance_prompt(
        body: EnhanceRequest,
        x_client_name: str | None = Header(None, alias="X-Client-Name"),
        x_privacy_level: str | None = Header(
            None, alias="X-Privacy-Level",
        ),
    ):
        """
        Enhance a prompt via Ollama.

        Headers:
            X-Client-Name: Client identifier for rule selection
            X-Privacy-Level: Privacy override (can only downgrade)
        """
        svc = get_enhancement_service()
        if not svc:
            raise HTTPException(503, "Enhancement service not initialized")

        privacy_override = None
        if x_privacy_level:
            try:
                privacy_override = PrivacyLevel(x_privacy_level)
            except ValueError:
                logger.warning(
                    f"Invalid X-Privacy-Level header: {x_privacy_level}"
                )

        result = await svc.enhance(
            prompt=body.prompt,
            client_name=x_client_name,
            bypass_cache=body.bypass_cache,
            privacy_override=privacy_override,
        )

        return {
            "original": result.original,
            "enhanced": result.enhanced,
            "model": result.model,
            "cached": result.cached,
            "was_enhanced": result.was_enhanced,
            "privacy_level": result.privacy_level,
            "provider": result.provider,
            "error": result.error,
        }

    @router.get("/ollama/stats")
    async def enhancement_stats():
        """Get enhancement service statistics."""
        svc = get_enhancement_service()
        if not svc:
            raise HTTPException(503, "Enhancement service not initialized")
        return await svc.get_stats()

    @router.post("/ollama/reset")
    async def reset_enhancement():
        """Reset enhancement service (clear cache and circuit breaker)."""
        svc = get_enhancement_service()
        if not svc:
            raise HTTPException(503, "Enhancement service not initialized")

        await svc.clear_cache()
        await svc.reset_circuit_breaker()
        return {"message": "Enhancement service reset"}

    return router
