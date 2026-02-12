"""
AgentHub Pipelines.

Pipelines chain multiple MCP servers and services together to accomplish
complex workflows like documentation generation and learning capture.
"""

from router.pipelines.documentation import DocumentationPipeline, DocumentationResult

__all__ = [
    "DocumentationPipeline",
    "DocumentationResult",
]
