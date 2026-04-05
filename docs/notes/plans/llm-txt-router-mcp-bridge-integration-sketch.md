# Plan: Integrate `llm.txt` with PromptHub Router and MCP Bridge

## Goal

Add a lightweight instruction-loading layer that reads project guidance from `~/prompthub/llm.txt` and task-specific companion docs such as `~/prompthub/docs/python-prompthub-guide.txt`, then injects that guidance into PromptHub's orchestration/enhancement flow before model calls.

The MCP bridge should remain transport-focused. It should not be responsible for prompt policy or repo guidance.

---

## Integration principle

Separate responsibilities clearly:

- **Router / orchestrator layer**
  - Detect whether the request is a coding or repo-assistance task.
  - Load `llm.txt` and any relevant companion guide.
  - Merge that guidance into the instruction context for the model.
- **Enhancement layer**
  - Optionally annotate or prioritize the guidance during prompt enhancement.
  - Preserve existing timeout, privacy, and fallback behavior.
- **MCP bridge layer**
  - Continue managing stdio transport, JSON-RPC, tool namespacing, and server lifecycle.
  - Do not parse or interpret `llm.txt` as part of bridge dispatch.

---

## Recommended insertion point

Best initial hook: **before OrchestratorAgent / EnhancementService model calls**.

Suggested flow:

1. Client request arrives at FastAPI route.
2. Route hands off to existing orchestration or enhancement service.
3. Service classifies the task:
   - coding / repo change / architecture question
   - generic non-code prompt
4. If coding-related:
   - load `~/prompthub/llm.txt`
   - load additional guide files based on task tags or file paths
5. Build the final instruction bundle:
   - base system prompt
   - project guidance from `llm.txt`
   - language/component guide(s)
   - user request
6. Send to the selected model through existing Ollama/OpenAI-compatible flow.
7. Preserve all existing privacy gating and fallback behavior.

---

## File-loading policy

### Always load

- `~/prompthub/llm.txt`

### Load conditionally

- `~/prompthub/docs/python-prompthub-guide.txt`
  - when task mentions Python, FastAPI, router, MCP bridge, OpenAI API, async, services, middleware, circuit breakers, or related files.

### Future optional files

Potential expansion later:

- `docs/audit-llm-guide.txt`
- `docs/memory-system-llm-guide.txt`
- `docs/openai-api-llm-guide.txt`

Keep V1 simple: one global file plus one Python-specific file.

---

## Proposed service sketch

Add a new service, for example:

- `router/services/repo_guidance.py`

Responsibilities:

- Discover guidance files.
- Decide which files apply to a task.
- Read and cache file contents.
- Return a structured instruction bundle.

Example sketch:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import asyncio
import time


@dataclass(slots=True)
class GuidanceBundle:
    system_sections: list[str]
    sources: list[str]


class RepoGuidanceService:
    def __init__(self, project_root: Path, ttl_seconds: int = 30) -> None:
        self.project_root = project_root
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, str]] = {}
        self._lock = asyncio.Lock()

    async def build_bundle(self, task_text: str, tags: set[str] | None = None) -> GuidanceBundle:
        tags = tags or set()
        sections: list[str] = []
        sources: list[str] = []

        llm_txt = self.project_root / "llm.txt"
        if llm_txt.exists():
            content = await self._read_cached(llm_txt)
            sections.append(content)
            sources.append(str(llm_txt))

        lowered = task_text.lower()
        python_signals = {
            "python", "fastapi", "async", "mcp", "bridge", "router",
            "openai api", "ollama", "pydantic", "httpx", "circuit breaker",
        }

        if tags.intersection({"python", "repo-code", "mcp"}) or any(s in lowered for s in python_signals):
            python_guide = self.project_root / "docs" / "python-prompthub-guide.txt"
            if python_guide.exists():
                content = await self._read_cached(python_guide)
                sections.append(content)
                sources.append(str(python_guide))

        return GuidanceBundle(system_sections=sections, sources=sources)

    async def _read_cached(self, path: Path) -> str:
        key = str(path)
        now = time.time()

        async with self._lock:
            cached = self._cache.get(key)
            if cached and (now - cached[0] < self.ttl_seconds):
                return cached[1]

            content = path.read_text(encoding="utf-8")
            self._cache[key] = (now, content)
            return content
```

---

## Orchestrator integration sketch

Add a small call near the orchestration or enhancement entrypoint.

Example shape:

```python
async def prepare_model_input(user_prompt: str, task_tags: set[str]) -> dict:
    guidance = await repo_guidance_service.build_bundle(
        task_text=user_prompt,
        tags=task_tags,
    )

    system_parts = [BASE_SYSTEM_PROMPT]
    system_parts.extend(guidance.system_sections)

    return {
        "system_prompt": "\n\n---\n\n".join(system_parts),
        "user_prompt": user_prompt,
        "guidance_sources": guidance.sources,
    }
```

Then feed `system_prompt` into the existing Ollama/OpenAI-compatible request path.

---

## MCP bridge integration rule

Do **not** thread `llm.txt` through bridge transport methods such as:

- raw stdio dispatch
- JSON-RPC framing
- tool execution internals
- per-server transport adapters

Instead:

- Use `llm.txt` to shape the model's planning and coding behavior before tool use starts.
- Let the bridge expose tools exactly as it already does.

This keeps prompt policy separate from transport mechanics.

---

## Suggested task tagging

If PromptHub already produces orchestrator metadata, add lightweight task tags like:

- `python`
- `repo-code`
- `mcp`
- `openai-api`
- `docs`
- `sensitive-config`

These tags can drive selective loading of guide files without making file discovery logic too magical.

---

## Safety notes

When guidance is loaded:

- Do not let it override explicit user instructions unless they conflict with security constraints.
- Treat `llm.txt` as advisory project policy, not as executable configuration.
- Log which guidance files were loaded for observability, but do not log their full contents on every request.
- Add tests to verify that missing guide files fail open rather than breaking requests.

---

## V1 implementation checklist

- [ ] Add `RepoGuidanceService`.
- [ ] Load `llm.txt` for coding/repo tasks.
- [ ] Load `python-prompthub-guide.txt` for Python/router/MCP/API tasks.
- [ ] Inject guidance into orchestrator/enhancement model input.
- [ ] Add lightweight TTL cache for file reads.
- [ ] Log loaded guidance file paths.
- [ ] Add tests for present/missing/stale cache cases.
- [ ] Add tests confirming MCP bridge behavior is unchanged.

---

## Nice-to-have later

- Directory-scoped `llm.txt` support, e.g. nearest file wins for submodules.
- More guide files for audit, memory, and API compatibility.
- A debug endpoint showing which guidance files would load for a given task.
- File hash tracking instead of TTL-only cache invalidation.

---

## Recommendation

Implement this as a router-side instruction loader in the orchestration/enhancement path, not as part of MCP transport. That gives agents repo-specific context before they plan changes, while keeping FastMCPBridge focused on stdio lifecycle, JSON-RPC dispatch, and tool namespacing.
