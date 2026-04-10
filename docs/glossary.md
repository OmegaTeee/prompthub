# PromptHub Glossary

> Canonical definitions for terms used across documentation, configs, and code.
> When in doubt about naming, check here first.

## Architecture & Roles

### PromptHub

The project itself. A local MCP router with prompt enhancement middleware, running on `localhost:9090`. Not a gateway (doesn't consolidate tools), not just a bridge (does more than transport translation). Best described as an **MCP service mesh for a single machine**.

### Router

The core FastAPI application (`app/router/`). Receives requests, applies cross-cutting concerns (auth, circuit breakers, caching, audit), and forwards them to the appropriate backend. The router does not modify the tool contract — clients see every MCP tool individually.

### Bridge (`prompthub-bridge`)

The Node.js stdio process (`mcps/prompthub-bridge.js`) that aggregates all MCP servers behind a single stdio interface. Translates between the MCP stdio transport (what clients speak) and PromptHub's HTTP endpoints (what the router exposes). Named `prompthub-bridge` in client MCP configs.

Use **bridge** when referring to:
- The MCP connection a client uses to reach PromptHub's tools
- The stdio process itself
- Client-side `mcp.json` entries

### Proxy (`prompthub-proxy`)

The OpenAI-compatible `/v1/` endpoint that intercepts, enhances, and forwards LLM requests to the backend model server (LM Studio). Named `prompthub-proxy` in client provider configs. Not a transparent pass-through — it mutates requests via the enhancement pipeline.

Use **proxy** when referring to:
- The `/v1/chat/completions` and `/v1/responses` endpoints
- Client-side provider/model configs pointing at `localhost:9090/v1`
- The auth + enhance + forward pipeline for LLM requests

### Gateway

**Not what PromptHub is.** A gateway consolidates and abstracts backend tools into a different client-facing contract (e.g., MCPGateway merges 300+ tools into 19 super-tools). PromptHub routes transparently. Avoid this term when describing PromptHub.

### Hub

Acceptable but imprecise. Describes the network topology (central point connecting spokes) but not the value-add. Prefer **router** for the technical component and **PromptHub** for the project.

## Enhancement & Privacy

### Enhancement

The process of rewriting a user's prompt through a local LLM before forwarding it to the target AI or model server. Controlled per-client via `enhancement-rules.json`. Enhancement is the core differentiator of PromptHub — it's what makes it more than a proxy.

### Enhancement rules

Per-client configuration in `app/configs/enhancement-rules.json` defining:
model, system prompt, temperature, max_tokens, and privacy_level. Clients
share the same default enhancement model today, but can still have different
rewriting policies and safety/privacy settings.

### Privacy level

The `PrivacyLevel` enum (`local_only`, `free_ok`, `any`) controlling whether a prompt may leave localhost. Set per-client in enhancement rules and overridable per-request via `X-Privacy-Level` header.

| Level | Meaning |
|---|---|
| `local_only` | Never leaves localhost. No cloud fallback. |
| `free_ok` | May use free-tier cloud (OpenRouter) as fallback. |
| `any` | May use any cloud provider. |

### Cloud fallback

When the local LLM server (LM Studio) is unavailable, `free_ok` and `any` clients fall back to OpenRouter free-tier models. `local_only` clients get no enhancement rather than leaking prompts. See ADR-007.

### Token budget

The `TokenBudget` cap (4,096 tokens) on enhancement input. Prevents wasting LLM context on rewriting very long prompts. Truncates at word boundaries with a notice appended.

## MCP Concepts

### MCP (Model Context Protocol)

The protocol that connects AI clients to tool servers. PromptHub manages MCP servers and proxies their JSON-RPC traffic.

### MCP server

A process that exposes tools (and optionally resources/prompts) via JSON-RPC. PromptHub manages 9 servers defined in `app/configs/mcp-servers.json`. Each runs as a stdio child process.

### Tool

A function exposed by an MCP server that an AI model can call. Tools have a name, description, and JSON Schema for input parameters. Example: `desktop-commander` exposes `read_file`, `execute_command`, etc.

### Tool prefix

The bridge prepends the server name to each tool name (`{server}_{tool}`) to avoid collisions across servers. Example: `desktop-commander_read_file`.

### Schema minification

The bridge strips verbose fields (`description`, `title`, `examples`, `default`) from tool `inputSchema` before sending to clients, reducing context usage by ~67%. Controlled via `MINIFY_SCHEMAS` env var.

### Tool registry

SQLite-backed cache (`app/router/tool_registry/`) storing raw MCP tool definitions pre-minification. Serves cached tools on subsequent `tools/list` requests (24h TTL). Archives old snapshots for historical access.

### Progressive disclosure

*(Planned — see `docs/notes/plans/progressive-tool-disclosure.md`)*

Two-tier tool loading: tier-1 tools (per-client essentials) are always visible; tier-2 tools are discoverable via a `discover_tools` meta-tool and loaded on demand via `load_server_tools`. Reduces initial tool context by ~80%.

## Resilience

### Circuit breaker

State machine protecting against cascading failures. Three states:

| State | Behavior |
|---|---|
| **CLOSED** | Requests pass through normally. |
| **OPEN** | Requests rejected immediately (503). Entered after 3 consecutive failures. |
| **HALF_OPEN** | One probe request allowed after 30s cooldown. Success → CLOSED, failure → OPEN. |

### L1 / L2 cache

Two-tier caching: L1 is an in-memory LRU cache (fast, volatile), L2 is a SQLite persistent cache (survives restarts). Write-through: writes go to both, reads check L1 first.

## Client Concepts

### Client

Any application that connects to PromptHub — either via the bridge (MCP tools) or the proxy (LLM completions). Each client has a name (e.g., `claude-desktop`, `raycast`, `cherry-studio`) used for enhancement rules, API key mapping, and audit logging.

### Client directory

A folder under `clients/{name}/` containing that client's configuration files: `mcp.json` (bridge config), provider configs, `setup.sh` (install script), `README.md`, and optionally a `*-llm.txt` knowledge file.

### llm.txt

A knowledge file (`{name}-llm.txt`) in a client's directory providing project context for LLM agents using that client. Read passively by tools like Desktop Commander or Perplexity. Not injected by the router.

## Infrastructure

### LM Studio

The local model server running on `localhost:1234`. Provides an OpenAI-compatible API. Hosts the enhancement model (`qwen3-4b-instruct-2507`) and the orchestrator model (`qwen3-4b-thinking-2507`).

### Orchestrator

The intent classification agent (`app/router/orchestrator/`) that analyzes prompts before enhancement. Uses the thinking model variant for chain-of-thought reasoning. Classifies intent, suggests tools, and annotates prompts. See ADR-009.

### LaunchAgent

The macOS daemon (`com.prompthub.router`) that runs the router as a background service. Managed via `launchctl`. Logs to `logs/`.

### Data directory (`~/.prompthub/`)

Persistent storage root for all SQLite databases, audit logs, and checksums. Configurable via `DATA_DIR` env var. Individual paths overridable per-database.
