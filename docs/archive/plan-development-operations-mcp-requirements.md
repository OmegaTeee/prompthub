---
title: "Development Operations MCP Requirements"
status: review
created: 2026-08-12
updated: 2026-08-12
tags: [mcp, developer-operations, shell, policy, catalog, worktrees]
---

# Development Operations MCP Requirements

## Summary

Build a standalone TypeScript MCP server that provides a small, stable set of
developer-operations capabilities to PromptHub clients. The server is a shared
tool-contract, command-library, and execution-policy layer for local executor
models and frontier orchestrators.

The MVP must improve task completion and token efficiency without exposing an
unrestricted shell. It must return bounded, structured results and reject
operations outside configured workspaces or reviewed command policies.

The server will run as a PromptHub-managed stdio child process. PromptHub will
continue to own server registration, lifecycle, routing, circuit breakers, and
tool disclosure. The Development Operations MCP will own workspace discovery,
execution policy, capability contracts, and command behavior.

## Context

PromptHub is the centralized MCP router and configuration source of truth for
multiple clients. The Development Operations MCP must serve clients such as:

- Codex as the central planner and frontier orchestrator.
- Ornith 1.0 as a local repository-level executor.
- OpenHands as an execution and repair harness.
- Goose and VS Code as additional MCP consumers.

The intended long-term workflow includes bounded repository maintenance,
documentation generation, Git operations, configuration validation, and
project-environment preparation. The foundation described here does not grant
agents autonomous destructive access or implement an unbounded self-healing
loop.

## Goals

1. Establish versioned, typed capability contracts shared by all MCP clients.
2. Centralize command definitions and execution policy.
3. Reduce token use with compact schemas and bounded structured output.
4. Provide safe workspace, Git, documentation, and catalog operations.
5. Support isolated Git worktrees for later repair workflows.
6. Keep implementation modular so higher-level workflows can compose existing
   capabilities without bypassing policy.
7. Fail locally and predictably without disrupting PromptHub or other managed
   MCP servers.

## Non-goals for the MVP

- Arbitrary shell access.
- Autonomous commit, push, merge, reset, branch deletion, or worktree removal.
- Package installation or mutation of global development tooling.
- Docker daemon mutation, image builds, or devcontainer provisioning.
- Automatic repair loops or unattended repository modification.
- A complete Catalog Object storage or workflow engine.
- Per-model authorization based on a caller-provided role.
- Replacing PromptHub's MCP router, server supervisor, or tool registry.
- Replacing OpenHands, Codex, or another client-side agent harness.

## Architectural boundary

```text
Codex / OpenHands / Ornith / Goose / VS Code
                       |
                       v
                PromptHub Router
       lifecycle, routing, breaker, disclosure
                       |
                       | stdio
                       v
          Development Operations MCP
       registry -> policy -> capabilities
                       |
              workspace/git/docs/process
```

### PromptHub responsibilities

- Register and supervise the MCP server.
- Start, stop, restart, and report server health.
- Proxy MCP requests through existing bridge and gateway paths.
- Apply circuit breakers and progressive tool disclosure.
- Preserve cross-client naming and configuration conventions.

### Development Operations MCP responsibilities

- Publish compact MCP tool definitions.
- Validate all tool input before performing work.
- Resolve and constrain workspace paths.
- Enforce command, environment, timeout, output, and mutation policies.
- Execute reviewed capability implementations.
- Normalize results and stable error codes.
- Load and query read-only catalog and project-document sources.
- Emit safe audit events and diagnostics.

## Proposed source layout

Use a standalone provider below the existing `mcps/` directory:

```text
mcps/devops-mcp/
|-- src/
|   |-- server.ts
|   |-- capabilities/
|   |-- policy/
|   |-- services/
|   |-- execution/
|   `-- catalog/
|-- config/
|   |-- commands.yaml
|   `-- policy.yaml
|-- catalog/
|-- schemas/
|-- tests/
|-- package.json
`-- tsconfig.json
```

The implementation must use services and dependency injection. It must not
collapse capability registration, policy, process execution, and filesystem
resolution into one `tools.ts` file.

## Capability contract

Every capability must register through a common typed contract. Runtime input
validation is required; TypeScript types alone are insufficient.

```ts
// mcps/devops-mcp/src/capabilities/capability.ts
interface Capability<TInput, TOutput> {
  id: string;
  version: string;
  category: string;
  summary: string;
  risk: "read" | "write" | "destructive";
  inputSchema: RuntimeSchema<TInput>;
  execute(
    input: TInput,
    context: ExecutionContext,
  ): Promise<CapabilityResult<TOutput>>;
}
```

The registry must reject duplicate `(id, version)` pairs and expose a
deterministically ordered capability list.

### Execution context

The trusted server runtime creates the execution context after resolving the
workspace and policy. The caller must not be able to provide or overwrite it.

```ts
interface ExecutionContext {
  requestId: string;
  workspaceId: string;
  workspaceRoot: string;
  signal: AbortSignal;
  policy: ResolvedPolicy;
}
```

### Result envelope

All capability calls must return a stable envelope:

```ts
interface CapabilityResult<T> {
  ok: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  };
  metadata: {
    durationMs: number;
    truncated: boolean;
    warnings: string[];
  };
}
```

Expected failures must be returned as structured results. Unexpected internal
failures may also produce an MCP error, but must not expose stack traces,
secrets, or uncontrolled command output.

## MVP capability set

Use portable MCP tool names externally and dotted identifiers internally.

| MCP tool | Internal capability | Risk | Purpose |
| --- | --- | --- | --- |
| `workspace_status` | `workspace.status` | Read | Detect repository, branch, worktree, and dirty state. |
| `worktree_list` | `workspace.worktree.list` | Read | List worktrees with normalized paths and branches. |
| `worktree_create` | `workspace.worktree.create` | Write | Create a worktree within the configured parent. |
| `git_status` | `git.status` | Read | Return a machine-readable repository summary. |
| `command_run` | `command.run` | Policy-dependent | Run one registered command profile. |
| `docs_search` | `docs.search` | Read | Search configured Markdown sources. |
| `docs_get` | `docs.get` | Read | Retrieve one document with bounded content. |
| `catalog_search` | `catalog.search` | Read | Search catalog metadata by text, tag, or type. |
| `catalog_get` | `catalog.get` | Read | Retrieve one catalog entry by ID and optional version. |
| `catalog_refresh` | `catalog.refresh` | Read/cache write | Atomically rebuild the in-memory catalog index. |

The external names avoid assuming that all MCP clients accept dotted tool
names. Internal dotted IDs preserve a stable namespace for future Catalog
Objects and workflow composition.

## Workspace service requirements

Implement one reusable `WorkspaceService`. Other capabilities must not
duplicate repository or path-resolution logic.

The service must:

- Resolve a caller-selected workspace from configured workspace IDs.
- Discover the repository root without traversing outside the configured root.
- Identify the active Git worktree and common Git directory.
- Locate configured documentation, wiki, catalog, and worktree roots.
- Normalize paths before returning them.
- Resolve user paths relative to the workspace, not the server process.
- Verify realpath containment after resolving symlinks.
- Reject traversal, symlink escape, missing roots, and ambiguous workspaces.

Absolute paths supplied by callers must be rejected unless a later reviewed
policy explicitly permits them.

## Command library and executor

### Command profiles

`command_run` must not accept a shell string or executable name. It accepts a
reviewed command ID and structured arguments:

```json
{
  "workspaceId": "prompthub",
  "commandId": "repository.search",
  "args": {
    "query": "CapabilityResult",
    "paths": ["src"],
    "maxMatches": 50
  }
}
```

The command library maps the ID to a fixed executable, validates arguments,
constructs an argument array, and invokes the process without a shell.

Initial command profiles should include:

- `repository.search`
- `git.diff`
- `git.diff-check`
- `test.named`
- `lint.named`
- `docs.validate`
- `config.validate`

Each profile must define:

- Stable ID and version.
- Description and risk level.
- Fixed executable resolution.
- Runtime argument schema.
- Allowed working-directory scope.
- Allowed environment variables.
- Timeout and output limits.
- Whether concurrent execution is safe.
- Expected exit-code handling.
- Result parser and truncation behavior.

### Process execution

The executor must:

- Spawn an executable with an argument array and `shell: false`.
- Use a resolved working directory contained in the selected workspace.
- Build a minimal environment from an allowlist.
- Enforce timeout and `AbortSignal` cancellation.
- Terminate the process group, including descendants, after cancellation.
- Capture stdout and stderr separately.
- Enforce byte limits while the process runs.
- Return exit code, signal, duration, truncation, and bounded output.
- Limit concurrency per workspace and globally.
- Reserve stdout for MCP JSON-RPC when the server uses stdio.
- Write operational logs only to stderr.

Pipes, redirects, command substitution, chained commands, glob expansion, and
shell metacharacter interpretation are prohibited in the MVP.

### RTK use

RTK may wrap commands whose human-readable output is returned directly to an
LLM. A service that parses output must use a stable machine-readable format
such as Git porcelain, NUL-delimited paths, or structured JSON. RTK filtering
must not alter data consumed by a parser.

## Git requirements

### Status

Git capabilities must prefer stable machine-readable output and normalize it
into structured fields. At minimum, status results must identify:

- Repository root.
- Current branch or detached HEAD.
- HEAD commit.
- Upstream branch when present.
- Ahead and behind counts when available.
- Staged, unstaged, untracked, conflicted, and ignored counts.
- Active worktree path.

### Worktree listing

`worktree_list` must return structured entries including path, HEAD, branch,
bare state, detached state, lock state, and prunable state where available.

### Worktree creation

`worktree_create` must:

- Accept a configured workspace, branch name, and optional start point.
- Validate Git references without interpolating them into a shell command.
- Create the worktree only below the configured worktree parent.
- Reject an existing target path or branch conflict.
- Return the created path, branch, HEAD, and warnings.
- Leave partial failures diagnosable without deleting unrelated data.

The MVP must not remove worktrees, delete branches, force checkout, or prune
worktree metadata.

## Documentation requirements

Repository-controlled Markdown is the primary project knowledge source.
External wiki, Obsidian, memory, and chat-derived material may be configured as
auxiliary sources but must not silently override reviewed repository documents.

### Search

`docs_search` must:

- Search configured documentation roots only.
- Support query, path, tag or document-kind filters where available.
- Return bounded snippets with document identifiers and relative paths.
- Use deterministic ranking and tie-breaking.
- Limit matches and snippet size.
- Report whether results were truncated.

### Retrieval

`docs_get` must:

- Resolve a document identifier through the configured index.
- Reject arbitrary filesystem paths.
- Return frontmatter, headings, relative path, and bounded body content.
- Support pagination or section selection for large documents.

### Indexing

The initial index may remain in memory. Index construction must be
deterministic and must report malformed frontmatter, duplicate identifiers,
unreadable files, and unsupported encodings without crashing the MCP server.

## Catalog loader requirements

The MVP catalog is read-only source data with an in-memory index. It is not a
permission database, workflow engine, or mutable knowledge store.

### Entry format

Each entry uses YAML frontmatter and a Markdown body:

```yaml
---
id: repository.search
version: 1
type: command
title: Repository Search
summary: Search tracked project content.
tags: [repository, search]
risk: read
---
```

Required behavior:

- Validate all required fields and supported values.
- Enforce unique `(id, version)` pairs.
- Index by ID, version, type, tag, and normalized text.
- Sort entries and search results deterministically.
- Return file-and-line diagnostics for invalid entries.
- Build a replacement index before swapping it into service.
- Retain the last valid index when a refresh fails.
- Read only from configured catalog roots.

Catalog metadata describes capabilities but does not authorize execution. Code
and reviewed policy configuration remain authoritative.

## Policy and security requirements

The default policy is least privilege and deny by default.

The MVP must provide:

- Configured workspace roots and worktree parents.
- Realpath containment checks after symlink resolution.
- Fixed executable paths or verified executable resolution.
- Command and argument allowlists.
- Environment-variable allowlisting.
- Secret-value and sensitive-path redaction.
- Timeouts, cancellation, output limits, and process-group cleanup.
- Global and per-workspace concurrency limits.
- Structured audit events without raw secret or command-output retention.
- Stable denial and validation error codes.
- Read-only defaults for newly registered capabilities.

The MVP must explicitly deny:

- Arbitrary executables and raw shell commands.
- Commands with pipes, redirects, substitutions, or chaining.
- File access outside configured roots.
- Commit, push, merge, rebase, reset, clean, branch deletion, or force actions.
- Worktree removal and pruning.
- Package-manager installation and global tooling mutation.
- Docker socket or daemon mutation.
- Credential discovery, display, export, or persistence.

## Caller identity and authorization

Labels such as `frontier-orchestrator` and `staff-ops-executor` describe agent
roles but are not trusted security identities. A role field supplied by an LLM
or MCP caller is forgeable and must not increase privileges.

Until PromptHub propagates authenticated client identity, the server must apply
one least-privilege policy to all callers. A later release may adopt one of
these designs:

1. PromptHub propagates a trusted authenticated client identity.
2. Separate read-only and operator instances expose different tool sets.
3. A trusted approval service issues short-lived authorization for mutations.

Per-agent privilege isolation must not be claimed until one of these trust
boundaries is implemented and tested.

## Token-efficiency requirements

- Keep MCP tool descriptions short and action-oriented.
- Use small input schemas with shared concepts represented consistently.
- Return structured summaries instead of unbounded terminal transcripts.
- Require explicit pagination or artifact retrieval for large results.
- Include truncation metadata and guidance for requesting the next segment.
- Avoid registering one tool per underlying shell command.
- Preserve compatibility with PromptHub progressive tool disclosure.
- Keep verbose diagnostics out of normal successful results.

## Reliability and service-isolation requirements

- One failed capability call must not terminate the MCP process.
- One failed MCP process must not interrupt PromptHub's other managed servers.
- Startup must validate configuration before advertising affected tools.
- Invalid optional catalog content must preserve the last valid index.
- Timeouts and cancellation must release process and concurrency resources.
- Errors must identify whether retry is safe.
- Logs must include a request ID and capability ID.
- Health behavior must integrate with PromptHub's existing supervisor and
  circuit-breaker model rather than creating a second router.

## Configuration requirements

Separate configuration by responsibility:

- `config/policy.yaml` defines workspace roots, worktree parents, limits,
  environment rules, and capability enablement.
- `config/commands.yaml` defines reviewed command profiles.
- `catalog/` contains descriptive Markdown/YAML entries.

Configuration must support environment-specific path values without storing
plaintext credentials. Invalid required configuration must fail startup with a
clear stderr diagnostic and non-zero exit. Optional catalog validation errors
may degrade to the last valid index.

## Audit requirements

Record one structured event per capability invocation with:

- Timestamp and request ID.
- Capability ID and version.
- Workspace ID.
- Risk class and policy decision.
- Duration, exit status, and truncation state when applicable.
- Stable error code when the operation fails.

Do not retain full prompts, raw command output, environment values, credential
material, or arbitrary document bodies in the audit event.

## Deferred self-healing workflow

Repository self-healing is a later workflow composed from reviewed
capabilities. Its target shape is:

```text
inspect -> plan -> isolated worktree -> bounded edits
        -> targeted verification -> diff summary -> human approval
```

Before implementation, that workflow must add:

- Maximum iteration, wall-time, and output budgets.
- Allowed-file and allowed-capability scopes.
- A required isolated worktree for write operations.
- Explicit success and rollback criteria.
- Verification selected from registered command profiles.
- Human approval before commit, push, merge, deployment, or cleanup.
- A terminal failure state that prevents endless repair loops.

## Deferred devcontainer support

Begin later container work with read-only capabilities:

- `environment.inspect`
- `devcontainer.validate`
- `devcontainer.plan`

Defer `devcontainer.create`, `devcontainer.build`, and direct Docker mutation.
Docker daemon access is a privileged boundary and requires a separate threat
model and approval design.

Preserve the environment ownership boundary:

- Keep Colima and Docker controls, VS Code, Keychain-backed secrets, and local
  model servers on macOS.
- Keep project runtimes, dependencies, compilers, linters, tests, and project
  CLIs in project-owned devcontainers.
- Use explicit service contracts such as `host.docker.internal` when a
  container must reach an approved host service.
- Do not construct containers by copying the host `PATH` or global tool state.

## Testing requirements

### Unit tests

At minimum, cover:

- Capability registration and duplicate rejection.
- Runtime input validation.
- Workspace root and worktree detection.
- Path traversal and symlink escape rejection.
- Command-profile resolution and argument validation.
- Timeout, cancellation, output truncation, and process cleanup.
- Git status and worktree parser fixtures.
- Catalog parsing, duplicate IDs, invalid frontmatter, and atomic refresh.
- Documentation search limits and deterministic ordering.
- Secret and sensitive-path redaction.

### Integration tests

At minimum, cover:

- MCP startup and `tools/list` discovery.
- One successful read-only command.
- One denied unknown command.
- Workspace and Git status in a temporary repository.
- Worktree creation inside the configured parent.
- Worktree creation denial outside the configured parent.
- Documentation search and retrieval.
- Catalog search, retrieval, and failed-refresh fallback.
- Timeout or cancellation without orphaned child processes.

### PromptHub validation

- Register the server in `app/configs/mcp-servers.json`.
- Start and inspect it through the PromptHub supervisor.
- Run the repository MCP validation workflow.
- Validate one successful proxied call.
- Validate at least one denied or failure-path call.
- Restart or fail the server and confirm other managed MCP servers continue to
  operate.

## Definition of done

The MVP foundation is complete when:

- PromptHub can start, supervise, stop, and restart the MCP server.
- MCP clients can discover the compact capability set through `tools/list`.
- Unknown command IDs and invalid arguments are rejected before process spawn.
- Workspace and Git status return normalized structured data.
- Repository documents can be searched and retrieved within configured roots.
- Catalog entries can be validated, searched, retrieved, and atomically
  refreshed.
- A Git worktree can be listed and created only under the configured parent.
- Timeouts, cancellation, output limits, and concurrency limits are enforced.
- Path traversal, symlink escape, denied-command, invalid-catalog, duplicate-ID,
  and worktree-boundary tests pass.
- PromptHub validation covers both a successful call and a failure path.
- Failure of this server does not interrupt PromptHub's other managed servers.
- User-facing and agent-facing documentation describe configuration, command
  registration, validation, and the deferred security boundaries.

## Implementation sequence

1. Create the TypeScript package, MCP lifecycle, logging, and test harness.
2. Implement the capability registry, runtime schemas, result envelope, and
   stable errors.
3. Implement `WorkspaceService` and path-containment policy.
4. Implement read-only workspace and Git capabilities.
5. Implement the command registry and constrained executor.
6. Implement documentation indexing, search, and retrieval.
7. Implement the read-only catalog loader and atomic refresh.
8. Implement constrained worktree creation.
9. Register the server with PromptHub and run success/failure integration tests.
10. Complete the repository documentation queue before declaring the feature
    complete.

## Decisions requiring ADR promotion

Promote these choices into one or more architecture decisions before or during
implementation:

- The Development Operations MCP is a standalone PromptHub-managed TypeScript
  provider rather than a module inside the Python router.
- Raw shell access is replaced by reviewed command profiles.
- Catalog metadata is descriptive and cannot grant execution permission.
- All callers share one least-privilege policy until trusted identity exists.
- Worktree creation is the only MVP repository mutation.
- Docker and autonomous self-healing remain outside the MVP trust boundary.

## Open questions

1. Should the first release expose write-risk tools to every PromptHub client,
   or run a separate operator instance for worktree creation?
2. Which repository documentation roots are canonical for each configured
   workspace?
3. Should large outputs use MCP resources, paginated tool results, temporary
   artifacts, or a combination?
4. Which command profiles are required for the first PromptHub repository
   workflow, and which are only future candidates?
5. Should command and policy configuration live with the MCP package or in a
   shared PromptHub configuration directory?
6. Which client identity can PromptHub authenticate and propagate without
   relying on model-provided fields?

