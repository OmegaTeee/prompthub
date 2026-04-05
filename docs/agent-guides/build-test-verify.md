# Build, test, and verify

This guide defines how coding agents should validate changes in PromptHub.
Use the smallest effective validation step first, then expand only as needed.
Prefer repo wrapper commands in `~/prompthub/scripts` when they exist and accurately reflect the intended workflow.

## Validation principles

- Start with the narrowest check that matches the files changed.
- Prefer documented repo wrapper commands over ad hoc direct commands when both are available.
- Do not claim success unless the relevant command completed or the generated output was inspected.
- If config generation changes, validate the generated artifact for the affected client.
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

Use when modifying client configuration generation, templates, naming, or output shape.

Recommended flow:

1. Identify the source file or generator.
2. Regenerate or rebuild the affected config output if the workflow supports generation.
3. Inspect the generated result for the affected client.
4. Check that shared naming and env var conventions still align across clients.
5. Update docs if user-facing behavior changed.

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
When a wrapper command exists in `scripts/`, prefer it.

### Install

```bash
# Python app dependencies
cd ~/prompthub/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# MCP / Node dependencies
cd ~/prompthub/mcps
npm install
```

### Start the router

Wrapper command:

```bash
cd ~/prompthub
./scripts/prompthub-start.zsh
```

Direct dev command:

```bash
cd ~/prompthub/app
source .venv/bin/activate
uvicorn router.main:app --reload --port 9090
```

### Stop the router

Wrapper command:

```bash
cd ~/prompthub
./scripts/prompthub-kill.zsh
```

### Health check

```bash
curl http://localhost:9090/health
```

### Tests

Primary wrapper command:

```bash
cd ~/prompthub
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh all
./scripts/test.sh coverage
./scripts/test.sh watch
```

Default behavior note:

```bash
cd ~/prompthub
./scripts/test.sh
```

This runs unit tests by default.

Equivalent direct unit-test command:

```bash
cd ~/prompthub/app
source .venv/bin/activate
python3 -m pytest tests/unit/ -v --tb=short
```

### Integration test server requirement

Integration tests require a live PromptHub server on port 9090.
Use one of these:

```bash
cd ~/prompthub
./scripts/prompthub-start.zsh
```

or

```bash
cd ~/prompthub/app
source .venv/bin/activate
uvicorn router.main:app --port 9090
```

### Lint

```bash
cd ~/prompthub/app
source .venv/bin/activate
python3 -m ruff check .
```

### Typecheck

```bash
cd ~/prompthub/app
source .venv/bin/activate
python3 -m mypy router cli
```

### MCP validation

```bash
cd ~/prompthub
./scripts/router/validate-mcp-servers.sh
```

### Restart MCP servers

```bash
cd ~/prompthub
python3 scripts/router/restart_mcp_servers.py
python3 scripts/router/restart_mcp_servers.py --all
python3 scripts/router/restart_mcp_servers.py obsidian
```

This requires the router running on `localhost:9090`.

### MCP package install or update

```bash
cd ~/prompthub/mcps
npm install <package-name>
```

### Python package install or update

```bash
cd ~/prompthub/app
source .venv/bin/activate
pip install -r requirements.txt
```

## Minimum expectations by change type

| Change type | Minimum validation |
| --- | --- |
| Docs only | Read affected docs for consistency and accuracy. |
| Small Python code change | Run the narrowest relevant lint, typecheck, or targeted test command. |
| Config generation or config-shape change | Inspect the affected config output and verify alignment with supported clients. |
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
