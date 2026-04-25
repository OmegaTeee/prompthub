# Model Profiles: fast / general / thinking / code

These profiles describe intended roles, constraints, and candidate models for PromptHub.
They are planning notes, not enforced routing rules yet.

## Fast

- Purpose: Lowest-latency responses for lightweight questions and UI glue.
- Priorities: Speed, low context use, acceptable (not perfect) depth.
- Typical tasks: Short Q&A, status checks, simple transformations, quick summaries.
- Constraints: Prefer < 512 token generations; avoid long chain-of-thought.
- Candidate models:
  - Small Qwen or similar 3–4B instruct models already used in PromptHub.
  - Same base model as “general” but with lower max_tokens and slightly higher temperature.

## General

- Purpose: Default assistant behavior for most prompts.
- Priorities: Balanced quality, speed, and resource use.
- Typical tasks: Mixed Q&A, explanation, small design decisions, non-critical planning.
- Constraints: Prefer < 1,024 token generations; allow moderate reasoning but no deep tool orchestration.
- Candidate models:
  - Current main enhancement model (qwen3-4b-instruct-2507 in LM Studio).
  - Other local instruct models with similar quality/VRAM footprint.

## Thinking

- Purpose: Higher-effort reasoning, decomposition, and orchestration.
- Priorities: Depth and correctness over latency.
- Typical tasks: Multi-step plans, complex tradeoff analysis, tool selection/orchestration.
- Constraints: Accept higher latency and longer outputs; must still respect local privacy levels.
- Candidate models:
  - Current orchestrator (qwen3-4b-thinking-2507) or successor models.
  - Reasoning-tuned local models that perform well on long chain-of-thought.

## Code

- Purpose: Code-centric tasks where structure and syntax correctness matter.
- Priorities: Accuracy, editor-aware output, minimal extraneous prose.
- Typical tasks: Implementing functions, refactors, small modules, test stubs, debug suggestions.
- Constraints: Output must be editor-friendly (clear fences, file hints, minimal narration).
- Candidate models:
  - Code-tuned Qwen or similar 7–8B models when VRAM allows.
  - The same “general” model, but with code-focused system prompts and lower temperature.
