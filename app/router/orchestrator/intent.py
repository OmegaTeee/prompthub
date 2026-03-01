"""
Intent classification models for the Orchestrator Agent.

Defines the structured output that qwen3:14b produces when
analyzing an incoming prompt before it reaches enhancement.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class IntentCategory(StrEnum):
    """Broad intent categories for routing decisions."""

    CODE = "code"                  # Code generation, debugging, review
    DOCUMENTATION = "documentation" # Docs, README, API reference
    SEARCH = "search"              # Web search, research, lookup
    MEMORY = "memory"              # Save/recall session context
    WORKFLOW = "workflow"          # Multi-step pipeline orchestration
    REASONING = "reasoning"        # Complex logic, planning, analysis
    GENERAL = "general"            # Catch-all for simple chat


class OrchestratorResult(BaseModel):
    """
    Structured output from the OrchestratorAgent.

    Carries intent classification, suggested tools, and an
    annotated prompt ready for the enhancement layer.
    """

    intent: IntentCategory = IntentCategory.GENERAL
    suggested_tools: list[str] = []
    context_hints: list[str] = []
    annotated_prompt: str = ""
    reasoning: str = ""            # Brief explanation (stripped from final prompt)
    confidence: float = 1.0        # 0.0–1.0 how confident the classification is
    skipped: bool = False          # True if orchestration timed out or errored
    error: str | None = None

    @classmethod
    def pass_through(cls, prompt: str, error: str | None = None) -> "OrchestratorResult":
        """Return a pass-through result when orchestration is skipped."""
        return cls(
            annotated_prompt=prompt,
            skipped=True,
            error=error,
        )


# Maps intent → preferred MCP servers to suggest
INTENT_SERVER_MAP: dict[IntentCategory, list[str]] = {
    IntentCategory.CODE: ["desktop-commander", "context7", "sequential-thinking"],
    IntentCategory.DOCUMENTATION: ["desktop-commander", "sequential-thinking", "context7"],
    IntentCategory.SEARCH: ["context7"],
    IntentCategory.MEMORY: ["memory"],
    IntentCategory.WORKFLOW: ["sequential-thinking", "desktop-commander"],
    IntentCategory.REASONING: ["sequential-thinking", "deepseek-reasoner"],
    IntentCategory.GENERAL: [],
}
