"""Pipeline orchestration endpoints."""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DocumentationRequest(BaseModel):
    """Request body for documentation generation."""

    repo_path: str
    project_name: str
    vault_path: str | None = None
    include_structure: bool = True


def create_pipelines_router(
    get_documentation_pipeline: Callable[[], Any],
) -> APIRouter:
    router = APIRouter(tags=["pipelines"])

    @router.post("/pipelines/documentation")
    async def run_documentation_pipeline(request: DocumentationRequest):
        """
        Generate documentation for a codebase.

        This pipeline:
        1. Creates a documentation prompt from the repo path
        2. Enhances it with LLM server (deepseek-r1)
        3. Optionally structures with Sequential Thinking
        4. Writes to Obsidian vault with Desktop Commander
        """
        pipeline = get_documentation_pipeline()
        if not pipeline:
            raise HTTPException(503, "Documentation pipeline not initialized")

        result = await pipeline.run(
            repo_path=request.repo_path,
            project_name=request.project_name,
            vault_path=request.vault_path,
            include_structure=request.include_structure,
        )

        return result.model_dump()

    return router
