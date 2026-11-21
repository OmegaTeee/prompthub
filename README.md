# PromptHub

A local MCP router for macOS. One service on `localhost:9090` runs your MCP servers, enhances prompts with a local LLM, and gives every AI client the same tools through a single bridge.

## What it does

- **MCP routing.** Runs a fleet of stdio MCP servers (context7, desktop-commander, memory, sequential-thinking, duckduckgo, Obsidian, and more) and exposes them through one endpoint. A Node bridge (`mcps/prompthub-bridge.js`) makes the fleet look like a single MCP server to clients.
- **Server-side client profiles.** Each client's model, tool disclosure (full or progressive), and privacy level live in `app/configs/enhancement-rules.json`. A client only needs its `CLIENT_NAME`.
- **Prompt enhancement.** A local model (LM Studio by default) rewrites prompts per client before they are forwarded. If the LLM is down, the original prompt passes through. Clients that allow it can fall back to OpenRouter's free tier.
- **OpenAI-compatible API.** `/v1/chat/completions`, `/v1/responses`, and `/v1/models` with bearer auth, so any OpenAI-compatible app can use your local models.
- **Resilience and observability.** Circuit breakers, an L1/L2 cache, a tool-schema cache, structured audit logging with tamper checks, and an HTMX dashboard at `/dashboard`.

## Quick start

Requirements: macOS, Python 3.11+, Node.js 20+, and LM Studio (or another OpenAI-compatible server) running on port 1234.

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # adjust LLM_HOST / LLM_PORT / models if needed
(cd ../mcps && npm install)          # MCP server packages

uvicorn router.main:app --reload --port 9090
curl http://localhost:9090/health
```

To connect a client, add the bridge to its MCP config. Claude Code example (`.mcp.json`):

```json
{
  "mcpServers": {
    "prompthub-bridge": {
      "command": "node",
      "args": ["/path/to/prompthub/mcps/prompthub-bridge.js"],
      "env": {
        "PROMPTHUB_URL": "http://127.0.0.1:9090",
        "CLIENT_NAME": "claude-code"
      }
    }
  }
}
```

[docs/guides/getting-started.md](docs/guides/getting-started.md) covers `/v1/` API tokens, the LaunchAgent daemon, and configs for other clients.

## Layout

```
app/        FastAPI router (router/), tests, runtime configs, dashboard templates, scripts
mcps/       Node stdio bridge + npm-installed MCP servers
docs/       Guides, architecture decisions (ADRs), OpenAPI spec, glossary
```

## Documentation

| Doc | For |
| --- | --- |
| [Getting started](docs/guides/getting-started.md) | Install, run, tokens, connecting clients |
| [Features](docs/guides/features.md) | Enhancement, memory, `/v1/` API, tool disclosure, privacy |
| [Operations](docs/guides/operations.md) | Troubleshooting, model choices, advanced config |
| [API spec](docs/api/openapi.yaml) | Every endpoint |
| [Architecture](docs/architecture/) | ADRs |
| [Glossary](docs/glossary.md) | Project terms |
| [AGENTS.md](AGENTS.md) | Developer and AI-agent conventions |

## Development

```bash
cd app && pytest tests/ -v
cd app && ruff check router/ && ruff format router/
cd app && mypy router/
```

Open PRs against `main`. Record user-visible changes under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE).
