# LM Studio Prompt Templates

These files are lightweight text presets for LM Studio task prompts. They are not model
prompt templates; they are reusable writing instructions you can paste into LM Studio
presets or task-specific chats.

## Files on disk

Current templates in this directory:

- `chat.txt`
- `code-documents.txt`
- `planner.txt`
- `pr-request.txt`
- `project-requirements.txt`
- `proof-read.txt`
- `qwick-text-editor.txt`
- `user-manual.txt`

## What changed in this set

The earlier versions were too generic to reliably shape good outputs. The current set is
designed to:

- use a consistent front matter shape across files
- allow enough tokens for useful output instead of forcing 50-token replies
- encode real workflow expectations such as filenames, risks, validation, and tradeoffs
- stay concise without collapsing into vague one-line answers

## Shared design rules

Each preset should:

- answer the task directly before adding extra detail
- include filenames or paths for code-related examples
- mention tradeoffs when more than one approach is reasonable
- surface common pitfalls early
- ask clarifying questions only when missing context blocks a correct answer
- keep beginner readability without removing technical precision

## When to use each preset

`chat.txt`
Use for general Q&A, technical help, and short decision support.

`project-requirements.txt`
Use when turning rough ideas into scope, deliverables, and acceptance criteria.

`planner.txt`
Use when the task needs a recommendation, ordered steps, tradeoffs, and likely files or validation points.

`pr-request.txt`
Use for PR descriptions, change requests, and review-ready summaries.

`user-manual.txt`
Use for step-by-step instructions aimed at beginners or mixed-skill users.

`code-documents.txt`
Use for code explanations, inline documentation drafts, and feature walkthroughs.

## Common pitfalls

- Setting `token_limit` too low, which produces unusably shallow answers
- Using the same tone and output shape for every task
- Omitting filenames, commands, or paths in technical guidance
- Asking clarifying questions too early instead of making a safe assumption
- Writing "concise" prompts that remove needed constraints

## Starter workflow

1. Copy the preset that matches the task.
2. Add repo- or project-specific context below it.
3. If the result is too broad, tighten the scope before lowering token limits.
4. If the result is too shallow, raise the token budget or ask for a comparison.

## Example adaptation

For repo work, extend a preset with lines such as:

- "Reference the latest best practices when they materially affect the recommendation."
- "Include filenames for implementation examples."
- "Compare two approaches if there is a meaningful tradeoff."
- "End with the next action or a focused follow-up question."
