# Project Admin Harness Design

Date: 2026-07-09

## Purpose

Define the PromptHub workflow orchestration harness so local and frontier agents
have clear responsibilities, safe contracts, and predictable handoffs.

The harness is intentionally not a high-autonomy coding boss. Codex and Claude
remain senior engineering surfaces. Ornith becomes the staff-operations copilot
behind a narrow MCP contract. Qwen3.5 Sushi Coder handles junior, bounded tasks.
Goose remains a local writing and execution adapter where its policies fit.

## Role Model

| Surface | Role | Authority |
| --- | --- | --- |
| Codex.app | Primary orchestration surface and senior engineer | Plans, edits, reviews, verifies, and explains user-facing decisions. |
| Claude | Alternate senior engineering surface | Same authority as Codex when chosen by the user. |
| Ornith via Project MCP | Staff-ops copilot, operations clerk, repo librarian | Gathers evidence, summarizes state, updates approved docs/memory, and reports risks. |
| Qwen3.5 Sushi Coder | Junior worker | Runs narrow unit-test, targeted-review, and reporting tasks with explicit scope. |
| Goose | Local ACP/writing helper | Writes markdown and runs approved local workflows through wrapper commands and recipes. |
| PromptHub MCP/router | Contract layer | Normalizes tools, routing, policy, logging, and client configuration. |

## Operating Principles

- Frontier agents own strategy. Ornith does not make product architecture or
  large implementation decisions.
- MCP tools are the contract between agents. The contract is stable even if the
  local model, runtime, or client changes.
- Tool outputs must be evidence-backed and cite files, commands, tests, or logs.
- Read-heavy workflows are auto-approved; writes require bounded targets and
  audit records; privileged actions require explicit user approval.
- Borrow OmO/LazyCodex discipline around planning, verification, and memory.
  Reject its incentive toward long-running autonomy.
- Keep the number of active orchestration surfaces small. Extra shells and
  dashboards stay experimental until they solve a concrete PromptHub problem.

## Borrowed Patterns From OmO/LazyCodex

The project should borrow these patterns locally:

- Plan-before-execute: classify task, gather evidence, propose action, execute
  bounded tools, verify result, then emit a state bundle.
- Verified completion: every worker report says what changed, what evidence
  supports success, what remains uncertain, and the next safe action.
- Memory as a first-class primitive: durable notes preserve decisions, known
  issues, test snapshots, documentation drift, and repo conventions.
- Compact context bundles: local workers summarize evidence before a frontier
  model spends tokens on it.
- Reusable workflow verbs: examples include `understand-repo`, `triage-tests`,
  `prepare-change`, `post-change-sync`, and `release-readiness`.

The project should reject these patterns:

- Long-running autonomous execution loops that continue without clear user or
  senior-agent checkpoints.
- Raw-shell exposure through a local model.
- Silent git mutation, branch movement, service restarts, migrations, deploys,
  or cross-project filesystem changes.
- Opaque agent steps that combine strategic planning, evidence gathering, and
  privileged execution in one black box.

## Project MCP Tool Contract

Phase 1 exposes five composable tools:

| Tool | Purpose | Default risk |
| --- | --- | --- |
| `project_query` | Answer project questions from docs, code, tests, git, and memory. | Auto-approved read-only. |
| `repo_search` | Run safe repository searches with path and result limits. | Auto-approved read-only. |
| `project_git` | Summarize status, diffs, recent commits, branch health, and draft commit text. | Auto-approved for summaries; approval-required for mutation. |
| `project_observe` | Run approved test, log, health-check, and failure-summary profiles. | Conditional by command profile. |
| `project_update` | Update approved memory, docs, ADR, changelog, runbook, test snapshot, or known-issues targets. | Conditional write with audit. |

All tool results use one compact result shape:

```json
{
  "summary": "string",
  "findings": [
    {
      "kind": "code|doc|test|log|memory|git|config",
      "path": "string",
      "line": 1,
      "note": "string",
      "evidence": "string"
    }
  ],
  "open_questions": ["string"],
  "next_actions": ["string"],
  "risks": ["string"],
  "confidence": "low|medium|high",
  "approval_mode": "auto|conditional|required"
}
```

## Safety Policy

### Auto-approved

- `rg`, `grep`, `fd`, and equivalent read-only search wrappers.
- `git status`, `git diff --stat`, limited `git diff`, and recent commit logs.
- Test discovery and static report summarization.
- Reading approved docs, memory, logs, and generated reports inside the project.

### Conditional

- Targeted test profiles such as focused `pytest`, `pnpm test`, or equivalent
  commands with timeouts.
- Documentation and memory updates inside approved paths.
- OKF validation and Obsidian-oriented markdown maintenance when path-bounded.

### Approval-required

- Git commits, branch creation, checkout, merge, rebase, tag, or push.
- File mutation outside approved docs or memory paths.
- Process restarts, docker actions, database migrations, deployment scripts.
- External network calls not covered by an explicit server/tool policy.

### Never Expose Directly

- Unrestricted shell.
- Destructive shell patterns.
- Secret retrieval outside a dedicated secret broker.
- Cross-project filesystem traversal.

## Audit Logging

Every Project MCP tool call emits a JSONL audit record containing:

- Timestamp and request id.
- Client and calling model when known.
- Tool name and normalized inputs with secrets redacted.
- Commands run, exit code, touched files, approval mode, and duration.
- Result summary and confidence.

Audit logs are part of the contract, not optional telemetry.

## Worker Delegation

Codex or Claude may delegate only bounded work:

- Ask Ornith for repo context, diff summaries, documentation drift, memory
  updates, release-note drafts, and test/log summaries.
- Ask Qwen3.5 Sushi Coder for junior tasks with explicit paths, commands, and
  expected report format.
- Ask Goose to write or split markdown only through approved wrappers, recipes,
  or hooks, preferably using Obsidian Tools MCP or OKF validation.

Delegated workers return evidence bundles. They do not silently decide the next
architecture move.

## Active Surface Decisions

### OmO and LazyCodex

OmO and LazyCodex are research inputs, not active dependencies. PromptHub should
study their harness patterns, borrow the safe local pieces, then uninstall or
disable the active OmO/LazyCodex hooks and agents from the Codex workflow.

The immediate cleanup target is `clients/codex/config.toml`, which currently
contains disabled OmO plugin entries, trusted hook-state entries, and LazyCodex
agent definitions. Removal should happen in a separate implementation step after
this spec is reviewed so unrelated local config drift is not accidentally
discarded.

### Agent UI

`app/agent-ui` is an Agno/AgentOS template shell, not PromptHub-native control
plane code. Keep it out of Phase 1.

The idea is worth preserving for a future PromptHub dashboard: website-project
administration, MCP server health, model routing, audit logs, docs workflows,
and bounded approval controls. That future dashboard should be PromptHub-native
or intentionally adapted, not adopted accidentally because a template exists.

## Phase 1 Scope

1. Capture this design in repo docs.
2. Remove or disable active OmO/LazyCodex workflow integration from Codex config
   after review.
3. Add a Project MCP implementation plan for the five-tool contract.
4. Keep Goose wrappers and OKF helpers available for markdown workflows.
5. Leave `app/agent-ui` untouched except for documenting its experimental status
   if needed.

## Out of Scope

- Implementing the full Project MCP server in this design step.
- Promoting `app/agent-ui` into a dashboard.
- Letting Ornith perform autonomous code edits.
- Enabling git mutation or deployment actions through local workers.
- Replacing Codex or Claude as the senior engineering surface.

## Success Criteria

- A future agent can read this spec and understand the role split without
  needing the prior chat context.
- PromptHub has one clear primary workflow: Codex or Claude orchestrates,
  Project MCP provides bounded local operations, and workers return evidence.
- OmO/LazyCodex cleanup has a clear target and does not remove the lessons worth
  keeping.
- The future dashboard idea is preserved without increasing current workflow
  sprawl.
