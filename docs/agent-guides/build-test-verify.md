# Build, test, and verify

This guide defines how coding agents should validate changes in PromptHub.
Use the smallest effective validation step first, then expand only as needed.
Run everything from the development checkout `~/workspaces/prompthub`, never the deployed one at `~/prompthub`. Prefer the wrapper commands in `app/scripts/` when they exist and match the intended workflow.

## Validation principles

- Start with the narrowest check that matches the files changed.
- Prefer documented repo wrapper commands over ad hoc direct commands when both are available.
- Do not claim success unless the relevant command completed or the generated output was inspected.
- If repo-managed client config files or setup scripts change, inspect the
  affected client file and verify the expected install target or workflow.
- If routing or transport behavior changes, validate both the happy path and at least one failure or fallback path.
- If documentation changes alter conventions, update both user-facing and agent-facing docs in the same change.

## Validation levels

### Small change

Use for minor docs edits, localized config changes, or low-risk code updates.

Recommended flow:

1. Run the most relevant lint, typecheck, or targeted validation command.
2. Inspect the changed files for consistency.
3. Confirm no unrelated generated output changed unexpectedly.

### Config change

Use when modifying client configuration files, setup scripts, naming, or output
shape.

Recommended flow:

1. Identify the source file in `app/configs/`.
2. Check the resolved result through the router, e.g. `GET /clients/{name}/tool-profile` or `/model-profile`.
3. Check that shared naming and env var conventions still align across clients.
4. Update docs if user-facing behavior changed.

### Routing change

Use when changing MCP routing, server registration, transport behavior, enhancement flow, or fallback logic.

Recommended flow:

1. Read the relevant architecture ADRs before editing behavior.
2. Run targeted tests first, then broader checks if needed.
3. Validate expected success behavior.
4. Validate at least one timeout, fallback, disabled, or error path.
5. Record any migration or compatibility risk in the final summary.

## Preferred repo commands

Use these commands as the default starting point for validation in this repository.
When a wrapper command exists in `app/scripts/`, prefer it.

### Install

```bash
# Python app dependencies
cd ~/workspaces/prompthub/app
python3.12 -m venv .venv   # 3.11 or 3.12, matching CI
source .venv/bin/activate
pip install -r requirements.txt

# MCP / Node dependencies
cd ~/workspaces/prompthub/mcps
npm install
```

### Start the router

Wrapper command:

```bash
cd ~/workspaces/prompthub
./app/scripts/prompthub-start.zsh
```

Direct dev command:

```bash
cd ~/workspaces/prompthub/app
source .venv/bin/activate
uvicorn router.main:app --reload --port 9090
```

### Stop the router

Wrapper command:

```bash
cd ~/workspaces/prompthub
./app/scripts/prompthub-kill.zsh
```

### Health check

```bash
curl http://localhost:9090/health
```

### Tests

Primary wrapper command:

```bash
cd ~/workspaces/prompthub
./app/scripts/test.sh unit
./app/scripts/test.sh integration
./app/scripts/test.sh all
./app/scripts/test.sh coverage
./app/scripts/test.sh watch
```

Default behavior note:

```bash
cd ~/workspaces/prompthub
./app/scripts/test.sh
```

This runs unit tests by default.

Equivalent direct unit-test command:

```bash
cd ~/workspaces/prompthub/app
source .venv/bin/activate
python3 -m pytest tests/unit/ -v --tb=short
```

### Integration test router

Integration tests (`tests/integration/`, `tests/test_endpoints.py`) start their own router through the `live_router` fixture in `tests/conftest.py`: a free port, a throwaway `DATA_DIR`, and the repo's configs. They stop and start MCP servers, so they never use the daemon on `:9090`. The fixture shuts the router and its MCP servers down when the session ends.

To run them against a router you started yourself, set `PROMPTHUB_TEST_URL`:

```bash
PROMPTHUB_TEST_URL=http://127.0.0.1:9191 python3 -m pytest tests/integration/
```

### Network guard

An autouse fixture in `tests/conftest.py` fails any test that sends a real HTTP request through `httpx` to anything other than the test router. In-process clients (FastAPI `TestClient`, `ASGITransport`) are unaffected. When a test trips it, mock the call. Two markers relax it:

| Marker | Effect |
| --- | --- |
| `requires_llm` | The test may reach the local LLM server (live smoke tests). |
| `offline` | Real requests still fail with `httpx.ConnectError`, but the test passes; use it for tests of unreachable-server handling. |

### Lint

```bash
cd ~/workspaces/prompthub/app
source .venv/bin/activate
python3 -m ruff check .
```

### Typecheck

```bash
cd ~/workspaces/prompthub/app
source .venv/bin/activate
python3 -m mypy router
```

### MCP validation

```bash
cd ~/workspaces/prompthub
./app/scripts/router/validate-mcp-servers.sh
```

### Restart MCP servers

```bash
cd ~/workspaces/prompthub
python3 app/scripts/router/restart_mcp_servers.py
python3 app/scripts/router/restart_mcp_servers.py --all
python3 app/scripts/router/restart_mcp_servers.py obsidian
```

This requires the router running on `localhost:9090`.

### MCP package install or update

```bash
cd ~/workspaces/prompthub/mcps
npm install <package-name>
```

### Python package install or update

```bash
cd ~/workspaces/prompthub/app
source .venv/bin/activate
pip install -r requirements.txt
```

## Minimum expectations by change type

| Change type | Minimum validation |
| --- | --- |
| Docs only | Read affected docs for consistency and accuracy. |
| Small Python code change | Run the narrowest relevant lint, typecheck, or targeted test command. |
| Client config or config-shape change | Inspect the affected client file or setup workflow and verify alignment with supported clients. |
| Routing or transport change | Run targeted validation plus at least one fallback or failure-path check. |
| MCP server package or config change | Validate package/config changes and run MCP server validation if relevant. |
| Broad refactor | Run targeted checks first, then broader lint/test/typecheck coverage. |

## Output expectations

In the final summary, include:

- What was changed.
- What commands were run.
- What was inspected manually.
- Any clients, generators, docs, or router behaviors affected.
- Any remaining follow-up or migration risk.
