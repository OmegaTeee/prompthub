"""
Documentation Generation Pipeline.

This pipeline chains multiple MCP servers to generate documentation:
1. Enhance prompt with Ollama (deepseek-r1 for reasoning)
2. Structure content with Sequential Thinking
3. Write to Obsidian vault with Desktop Commander
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DocumentationResult(BaseModel):
    """Result of documentation generation."""

    status: str
    output_path: str
    obsidian_url: str | None = None
    content_length: int = 0
    error: str | None = None


class DocumentationPipeline:
    """
    Pipeline for generating documentation from codebases.

    Chains enhancement → structuring → file writing to produce
    well-formatted Markdown documentation in an Obsidian vault.

    Example:
        pipeline = DocumentationPipeline(
            enhancement_service=enhancement_service,
            supervisor=supervisor
        )
        result = await pipeline.run(
            repo_path="/path/to/project",
            project_name="My Project"
        )
    """

    def __init__(
        self,
        enhancement_service: Any,
        supervisor: Any,
        default_vault_path: str = "~/Obsidian/Projects",
    ):
        """
        Initialize the documentation pipeline.

        Args:
            enhancement_service: EnhancementService for Ollama calls
            supervisor: Supervisor for MCP server bridges
            default_vault_path: Default Obsidian vault path
        """
        self._enhancement = enhancement_service
        self._supervisor = supervisor
        self._default_vault_path = default_vault_path

    async def run(
        self,
        repo_path: str,
        project_name: str,
        vault_path: str | None = None,
        include_structure: bool = True,
    ) -> DocumentationResult:
        """
        Generate documentation for a codebase.

        Args:
            repo_path: Path to the repository
            project_name: Name for the documentation
            vault_path: Optional custom vault path
            include_structure: Whether to use Sequential Thinking for structure

        Returns:
            DocumentationResult with status and output path
        """
        vault = vault_path or self._default_vault_path
        vault = str(Path(vault).expanduser())

        try:
            # Step 1: Create documentation prompt
            doc_prompt = self._create_doc_prompt(repo_path, project_name)
            logger.info(f"Generating documentation for {project_name}")

            # Step 2: Enhance with Ollama
            enhanced_result = await self._enhancement.enhance(
                prompt=doc_prompt,
                client_name="documentation-pipeline",
            )

            if enhanced_result.error and not enhanced_result.was_enhanced:
                logger.warning(f"Enhancement failed: {enhanced_result.error}")
                # Fall back to original prompt
                content = doc_prompt
            else:
                content = enhanced_result.enhanced

            # Step 3: Structure with Sequential Thinking (optional)
            if include_structure:
                structured = await self._structure_content(content)
                if structured:
                    content = structured

            # Step 4: Format final document
            final_doc = self._format_document(
                project_name=project_name,
                content=content,
                repo_path=repo_path,
            )

            # Step 5: Write to Obsidian vault
            output_path = f"{vault}/{project_name}.md"
            write_success = await self._write_to_vault(output_path, final_doc)

            if write_success:
                obsidian_url = f"obsidian://open?vault=Projects&file={project_name}"
                logger.info(f"Documentation written to {output_path}")
                return DocumentationResult(
                    status="complete",
                    output_path=output_path,
                    obsidian_url=obsidian_url,
                    content_length=len(final_doc),
                )
            else:
                return DocumentationResult(
                    status="partial",
                    output_path=output_path,
                    content_length=len(final_doc),
                    error="Failed to write to vault, content generated successfully",
                )

        except Exception as e:
            logger.exception(f"Documentation pipeline failed: {e}")
            return DocumentationResult(
                status="failed",
                output_path="",
                error=str(e),
            )

    def _create_doc_prompt(self, repo_path: str, project_name: str) -> str:
        """Create the documentation generation prompt."""
        return f"""Generate technical documentation for the project at: {repo_path}

Project Name: {project_name}

Include the following sections:

## Architecture Overview
- High-level architecture description (max 500 words)
- Key design decisions and patterns used

## Setup Instructions
- Prerequisites and dependencies
- Installation steps with exact commands
- Configuration requirements

## Key Components
- Main modules and their responsibilities
- Important classes/functions with brief descriptions

## Common Workflows
- How to run the application
- How to run tests
- How to deploy (if applicable)

## API Reference (if applicable)
- Main endpoints or public interfaces
- Request/response formats

Format the output in clean Markdown with proper headers and code blocks.
Use [[wikilinks]] for cross-references to related concepts.
"""

    async def _structure_content(self, content: str) -> str | None:
        """
        Structure content using Sequential Thinking server.

        Returns structured content or None if structuring fails.
        """
        try:
            bridge = self._supervisor.get_bridge("sequential-thinking")
            if not bridge:
                logger.warning("Sequential Thinking server not available")
                return None

            response = await bridge.send(
                "tools/call",
                {
                    "name": "sequentialthinking",
                    "arguments": {
                        "thought": f"Organize and structure the following documentation into logical sections:\n\n{content}",
                        "thoughtNumber": 1,
                        "totalThoughts": 3,
                        "nextThoughtNeeded": True,
                    },
                },
            )

            if "result" in response:
                result = response["result"]
                if isinstance(result, dict) and "content" in result:
                    return result["content"][0].get("text", content)
                elif isinstance(result, str):
                    return result

            return None

        except Exception as e:
            logger.warning(f"Sequential Thinking structuring failed: {e}")
            return None

    def _format_document(
        self,
        project_name: str,
        content: str,
        repo_path: str,
    ) -> str:
        """Format the final documentation with frontmatter."""
        timestamp = datetime.now().isoformat()

        # Clean up content (remove thinking traces if present)
        if "<think>" in content:
            # Extract only the content after thinking
            parts = content.split("</think>")
            if len(parts) > 1:
                content = parts[-1].strip()

        return f"""---
tags: [project, documentation, auto-generated]
created: {timestamp}
source: {repo_path}
generator: agenthub-documentation-pipeline
---

# {project_name}

{content}

---

*Generated by AgentHub Documentation Pipeline*
*Source: {repo_path}*
*Created: {timestamp}*
"""

    async def _write_to_vault(self, path: str, content: str) -> bool:
        """
        Write content to Obsidian vault using Desktop Commander.

        Returns True if write succeeded, False otherwise.
        """
        try:
            bridge = self._supervisor.get_bridge("desktop-commander")
            if not bridge:
                logger.warning("Desktop Commander server not available")
                # Fall back to direct file write
                return self._direct_write(path, content)

            response = await bridge.send(
                "tools/call",
                {
                    "name": "write_file",
                    "arguments": {
                        "path": path,
                        "content": content,
                    },
                },
            )

            return "error" not in response

        except Exception as e:
            logger.warning(f"Desktop Commander write failed: {e}")
            # Fall back to direct file write
            return self._direct_write(path, content)

    def _direct_write(self, path: str, content: str) -> bool:
        """Direct file write fallback."""
        try:
            file_path = Path(path).expanduser()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            logger.info(f"Direct write to {path} succeeded")
            return True
        except Exception as e:
            logger.error(f"Direct write failed: {e}")
            return False
