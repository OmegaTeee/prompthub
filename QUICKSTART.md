# PromptHub Quickstart

Get PromptHub running and connected to your first app. This takes about five minutes.

PromptHub is a local router that connects your AI-powered apps to LM Studio models through one endpoint. Think of it like a power strip: you plug all your tools into one place, and PromptHub handles the wiring. (For precise definitions of terms like router, bridge, and proxy, see [docs/glossary.md](docs/glossary.md).)

---

## 1. Prerequisites

You need four things installed on your Mac before you start:

1. **Homebrew** — the macOS package manager. If you do not have it, visit [brew.sh](https://brew.sh).
2. **LM Studio** — runs AI models locally. Install it from https://lmstudio.ai/ and use the `lms` CLI to download a model. Example:
   ```bash
   # Download a model to the local LM Studio instance
   lms get <model-identifier>
   ```
3. **Node.js** — needed for MCP server packages and bridge tooling:
   ```bash
   brew install node
   ```
4. **Python 3.11+** — via `pyenv` or system Python.

---

## 2. Project Layout

```text
~/prompthub/
├── app/              # FastAPI router (Python)
├── scripts/          # prompthub-start.zsh, prompthub-kill.zsh, open-webui/, etc.
├── mcps/             # MCP bridge + package dependencies
├── docs/             # Developer docs, ADRs, and user guides
└── logs/             # Router logs
```

Router code and Python dependencies live under `app/`. MCP server package management and bridge-related Node assets live under `mcps/`. Shared operational wrappers live under `scripts/`.

---

## 3. Install Dependencies

From the repo root:

```bash
cd ~/prompthub

# Python app dependencies
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Node dependencies for MCP tooling
cd mcps
npm install
cd ..
```

---

## 4. Start PromptHub

Preferred wrapper command:

```bash
cd ~/prompthub
./scripts/prompthub-start.zsh
```

Alternative direct dev command:

```bash
cd ~/prompthub/app
source .venv/bin/activate
uvicorn router.main:app --reload --port 9090
```

Check health:

```bash
curl http://localhost:9090/health
```

---

## 5. Verify Scripts and MCP Setup

Validate MCP server commands and package availability:

```bash
cd ~/prompthub
./scripts/router/validate-mcp-servers.sh
```

Run tests with the current repo wrapper:

```bash
cd ~/prompthub
./scripts/test.sh
./scripts/test.sh integration
```

`./scripts/test.sh` runs unit tests by default. Integration mode requires the router to be running on port 9090.

---

## 6. Client Configuration

Client configs live in `clients/` — each client has its own directory with an `mcp.json` and a `setup.sh` script.

```bash
# Set up a client (creates symlink or prints instructions)
./clients/lm-studio/setup.sh
./clients/claude-desktop/setup.sh

# Check all clients and system health
./scripts/diagnose.sh
```

Sources of truth:

- `clients/<name>/mcp.json` for per-client MCP bridge configs.
- `app/configs/mcp-servers.json` for MCP server definitions.
- `app/configs/enhancement-rules.json` for prompt-enhancement behavior.

---

## 7. Stop PromptHub

```bash
cd ~/prompthub
./scripts/prompthub-kill.zsh
```

---

## 8. Common Commands

```bash
# Start / stop router
./scripts/prompthub-start.zsh
./scripts/prompthub-kill.zsh

# Validate MCP setup
./scripts/router/validate-mcp-servers.sh

# Restart MCP servers via router API
python3 scripts/router/restart_mcp_servers.py

# Run tests
./scripts/test.sh
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh all
./scripts/test.sh coverage

# Clean temp files
./scripts/dev/cleanup.sh --dry-run
```

---

## 9. Troubleshooting

- Router not responding: run `curl http://localhost:9090/health` and confirm PromptHub is started.
- Integration tests failing: ensure the router is running before `./scripts/test.sh integration`.
- MCP validation failures: run `./scripts/router/validate-mcp-servers.sh` and inspect `app/configs/mcp-servers.json`.
- LM Studio issues: confirm the LM Studio local server is running and reachable.

---

## 10. Next Steps

- Read `README.md` for project overview.
- Read `scripts/README.md` for wrapper commands.
- Read `docs/agent-guides/project-map.md` and `docs/agent-guides/build-test-verify.md` for repo workflow conventions.
