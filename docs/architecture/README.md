# Architecture Documentation

Technical architecture and decision history for PromptHub.

Use this document as the entry point for the current system shape.
For canonical terminology, see [the glossary](../glossary.md).

## Architecture Decision Records (ADRs)

ADRs document significant architectural decisions, the context behind them,
and their consequences.

### Active ADRs

- [ADR-001: Stdio Transport for MCP Servers](ADR-001-stdio-transport.md)
- [ADR-002: Circuit Breaker Pattern](ADR-002-circuit-breaker.md)
- [ADR-003: Per-Client Prompt Enhancement](ADR-003-per-client-enhancement.md)
- [ADR-004: Modular Monolith Architecture](ADR-004-modular-monolith.md)
- [ADR-005: Async-First Architecture](ADR-005-async-first.md)
- [ADR-006: Enhancement Timeout & Unified Model](ADR-006-enhancement-timeout.md)
- [ADR-007: Cloud Fallback via OpenRouter](ADR-007-cloud-fallback.md)
- [ADR-008: Task-Specific Models & Orchestrator Agent](ADR-008-task-specific-models.md)
- [ADR-009: Orchestrator Agent](ADR-009-orchestrator-agent.md)

### Deep Dives

- [MCP Transport Adapters](mcp-transport-adapters.md) — stdio bridge,
  Streamable HTTP gateway, internal FastMCP bridge

## System Overview

PromptHub is a local MCP router with two client-facing surfaces:

- **Bridge path**: AI clients connect to `prompthub-bridge` over stdio and see
  MCP tools aggregated from managed servers.
- **Proxy path**: OpenAI-compatible clients connect to `/v1/*` and receive
  prompt enhancement before the request is forwarded to LM Studio (or another
  OpenAI-compatible local LLM server).

At runtime, the system looks like this:

```text
┌───────────────┐      stdio       ┌────────────────────┐
│ MCP clients   │ ───────────────▶ │ prompthub-bridge   │
│ Claude,       │                  │ mcps/*.js          │
│ VS Code,      │                  └─────────┬──────────┘
│ Raycast       │                            │ HTTP
└───────────────┘                            ▼
                                     ┌────────────────────┐
┌───────────────┐      HTTP          │ PromptHub Router   │
│ Proxy clients │ ─────────────────▶ │ FastAPI :9090      │
│ LM Studio     │                    │ routes + services  │
│ Cherry Studio │                    └──────┬─────┬───────┘
│ custom apps   │                           │     │
└───────────────┘                           │     ├──────────────▶ MCP servers
                                            │     │                (stdio child
                                            │     │                processes)
                                            ▼
                                     LM Studio :1234
                                     OpenAI-compatible
                                     local model server
```

## Core Components

### Router

The FastAPI application in `app/router/` is the core of PromptHub. It owns:

- MCP server lifecycle management
- request routing and normalization
- prompt enhancement and cloud fallback
- circuit breaker enforcement
- session memory and tool registry endpoints
- dashboard and audit surfaces

The router is the central application component. It is not the same thing as
the stdio bridge, and it is not a gateway in the MCPGateway sense.

### Bridge (`prompthub-bridge`)

The Node.js bridge in `mcps/prompthub-bridge.js` exposes all configured MCP
servers as one stdio endpoint for desktop clients. It:

- translates stdio JSON-RPC into HTTP calls against the router
- aggregates tools from multiple servers
- prefixes tool names as `{server}_{tool}`
- minifies tool schemas before returning them to clients

### Proxy (`/v1/*`)

The OpenAI-compatible proxy in `router/openai_compat/router.py` exposes:

- `POST /v1/chat/completions`
- `POST /v1/responses`
- `GET /v1/models`

It authenticates clients, optionally enhances the last user message, and then
forwards the request to LM Studio using the same OpenAI-compatible wire format.

### Supervisor + Registry

The server-management layer in `router/servers/` owns:

- configured MCP server definitions
- child-process startup and shutdown
- auto-start for configured servers
- restarts and health-aware lifecycle transitions

### Enhancement Service

The enhancement layer in `router/enhancement/` owns:

- per-client enhancement rules from `enhancement-rules.json`
- LM Studio calls through a backend-agnostic OpenAI-compatible client
- privacy-level enforcement
- OpenRouter fallback when privacy policy allows it
- cache-backed prompt rewriting

### Orchestrator

The orchestrator in `router/orchestrator/` runs before enhancement and handles:

- intent classification
- prompt annotation
- suggested MCP server/tool hints
- session-context-aware pre-processing

The current model split is:

| Role | Model | Purpose |
|---|---|---|
| Enhancement | `qwen3-4b-instruct-2507` | Fast prompt rewriting |
| Orchestrator | `qwen3-4b-thinking-2507` | Intent classification and tool hints |

See [ADR-008](ADR-008-task-specific-models.md) and
[ADR-009](ADR-009-orchestrator-agent.md) for the full rationale.

### Tool Registry

The tool registry in `router/tool_registry/` caches raw MCP tool definitions in
SQLite before the bridge minifies them. This reduces repeated live `tools/list`
fan-out and supports archival of prior snapshots.

### Memory System

The memory system in `router/memory/` provides session-scoped facts, memory
blocks, and full session context assembly through `/sessions/*`.

## API Surfaces

PromptHub exposes several distinct surfaces:

| Surface | Primary endpoints | Purpose |
|---|---|---|
| Health and control | `/health`, `/servers/*`, `/circuit-breakers*` | Operational state and server lifecycle |
| MCP proxy | `/mcp/{server}/{path}` | Router-managed proxy to one MCP server |
| MCP HTTP gateway | `/mcp-direct/mcp` | Streamable HTTP MCP transport |
| Enhancement API | `/llm/enhance`, `/llm/orchestrate`, `/llm/stats` | Debugging and direct enhancement calls |
| OpenAI-compatible proxy | `/v1/chat/completions`, `/v1/responses`, `/v1/models` | LLM-compatible client integration |
| Memory API | `/sessions/*` | Session memory CRUD and context assembly |
| Tool registry API | `/tools/*` | Cached tool snapshots and maintenance |
| Dashboard | `/dashboard*` | HTMX operational UI |
| Audit and security | `/audit/*`, `/security/alerts*` | Audit inspection and anomaly views |
| Pipelines | `/pipelines/documentation` | Documentation workflow entry point |

## Request Flows

### 1. Stdio Bridge Tool Flow

Desktop MCP clients use the Node bridge, which calls back into the router:

```text
Client
  → prompthub-bridge (stdio)
  → GET /servers
  → POST /mcp/{server}/{path}
  → Supervisor / FastMCPBridge
  → stdio child process
  → tool result
```

Important properties:

- tools remain transparent, not consolidated into super-tools
- tool names are prefixed per server
- schema minification happens in the Node bridge, not in the Python router
- server start/stop/restart remains owned by the router

### 2. OpenAI-Compatible Proxy Flow

```text
Client
  → POST /v1/chat/completions or /v1/responses
  → Bearer-token auth
  → optional prompt enhancement
  → circuit breaker check
  → LM Studio /v1/*
  → proxied response
```

Key behavior:

- enhancement is non-fatal; failures degrade to the original prompt
- the proxy accepts the upstream model name from the client request
- the proxy and enhancement service share the same local LLM backend

### 3. Enhancement Flow

```text
Client
  → /llm/enhance or internal proxy helper
  → OrchestratorAgent.process()
  → EnhancementService.enhance()
  → cache lookup
  → LM Studio chat completion
  → optional OpenRouter fallback
  → enhanced prompt
```

Current enhancement behavior:

- orchestrator timeout target: 2.5s hard ceiling
- privacy gating:
  - `local_only` never leaves localhost
  - `free_ok` and `any` may use cloud fallback
- cloud fallback is controlled by [ADR-007](ADR-007-cloud-fallback.md)

### 4. MCP HTTP Gateway Flow

```text
Client
  → POST /mcp-direct/mcp
  → FastMCP Streamable HTTP session manager
  → dynamic client factory
  → Supervisor / FastMCPBridge
  → stdio child process
  → MCP response
```

This path exists for clients that speak MCP over HTTP instead of stdio.

## State and Resilience

### Server Lifecycle

PromptHub tracks MCP servers through explicit lifecycle states:

```text
STOPPED → STARTING → RUNNING
   ↑                     ↓
   └────── STOPPING ─────┘
             ↓
           FAILED
```

### Circuit Breakers

PromptHub uses circuit breakers for downstream protection:

```text
CLOSED → OPEN → HALF_OPEN → CLOSED
```

Typical behavior:

- failures trip the breaker after the configured threshold
- open breakers fail fast instead of waiting on dead downstreams
- half-open allows a probe request before normal traffic resumes

Circuit breakers protect:

- MCP server paths
- enhancement traffic
- orchestrator traffic
- OpenAI-compatible proxy forwarding
- OpenRouter fallback

### Caching Layers

PromptHub uses multiple caches for different concerns:

| Cache | Scope | Backing store |
|---|---|---|
| Enhancement cache L1 | prompt rewrites | in-memory LRU |
| Enhancement cache L2 | prompt rewrites | SQLite |
| Orchestrator cache | intent classification | in-process LRU |
| Tool registry cache | MCP tool snapshots | SQLite |

### Privacy and Fallback Rules

Enhancement rules are per client. Each rule controls:

- system prompt
- temperature
- max token budget
- privacy level

If LM Studio is unavailable:

- `local_only` clients skip enhancement and keep the original prompt
- `free_ok` and `any` may fall back to OpenRouter if enabled

## Design Principles

### Transparent Routing

PromptHub routes and enhances requests without inventing a new tool contract.
Clients still see MCP tools individually.

### Fail Safe by Default

If enhancement, orchestration, or a downstream service fails, the system
prefers graceful degradation over blocking the user.

### Async-First Boundaries

The router is built around async I/O:

- HTTP via `httpx`
- MCP subprocess traffic via FastMCP transports
- SQLite through `aiosqlite`

### Centralized Configuration

Behavior lives in shared config files such as:

- `app/configs/mcp-servers.json`
- `app/configs/enhancement-rules.json`
- `app/configs/api-keys.json`

The preference is to fix generators and shared config logic rather than patch
derived client output.

## Technology Stack

### Core

- Python 3.11+
- FastAPI
- Pydantic / pydantic-settings
- httpx
- Uvicorn

### MCP and Routing

- FastMCP Client
- Streamable HTTP MCP gateway
- Node.js stdio bridge (`prompthub-bridge`)
- JSON-RPC 2.0 / MCP

### Persistence and Observability

- SQLite / aiosqlite
- structlog-backed audit logging
- HTMX dashboard
- Prometheus instrumentation

### Local LLM Backend

- LM Studio on `localhost:1234`
- OpenAI-compatible API surface
- Apple Silicon-friendly local inference workflow

## Deployment and Operations

### Development

Typical local workflow:

```bash
cd ~/prompthub/app
source .venv/bin/activate
uvicorn router.main:app --reload --port 9090
```

Run LM Studio separately and ensure the required local models are loaded.

### Background Service

On macOS, PromptHub can run as a LaunchAgent using
`com.prompthub.router.plist`.

### Operational Assumptions

- single-user local machine
- localhost-only routing model by default
- MCP servers run as stdio child processes
- LM Studio is the default local inference backend

## Scaling Considerations

PromptHub is optimized for a single-machine workflow, not horizontal scale.
The current design assumes:

- one FastAPI router process
- local child processes for MCP servers
- local SQLite-backed persistence
- local LLM inference

If scaling becomes necessary, the likely pressure points are:

1. shared cache coordination across router instances
2. LLM throughput and model concurrency
3. centralizing audit and tool-registry storage
4. replacing local-only assumptions in dashboard and operations flows

## What This Document Does Not Do

This README intentionally avoids historical benchmark numbers and stale model
comparison tables. Those values drift quickly and belong in targeted ADRs,
tests, or operational notes tied to a specific date and environment.

For current naming and conceptual boundaries, prefer:

- [Glossary](../glossary.md)
- [ADR-007](ADR-007-cloud-fallback.md)
- [ADR-008](ADR-008-task-specific-models.md)
- [ADR-009](ADR-009-orchestrator-agent.md)
- [MCP Transport Adapters](mcp-transport-adapters.md)
