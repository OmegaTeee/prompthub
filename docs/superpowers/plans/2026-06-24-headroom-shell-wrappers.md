# Headroom Shell Wrappers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repo-local Headroom install easy to launch from the shell and reliable for Codex MCP startup.

**Architecture:** Keep the shell-facing entrypoints in `clients/dotfiles/shell_common.sh` so the repo’s shared environment knows where the Headroom venv lives and can launch proxy, doctor, and wrapped clients from one place. Point the Codex MCP server at the repo-local Headroom binary explicitly in `clients/codex/config.toml` so the MCP server does not depend on ambient shell PATH state.

**Tech Stack:** POSIX shell, TOML, Headroom CLI.

---

### Task 1: Add Headroom shell environment and wrappers

**Files:**
- Modify: `clients/dotfiles/shell_common.sh`

- [ ] **Step 1: Update the shared shell environment**

```sh
export HEADROOM_HOME="${HOME}/.local/share/prompthub/headroom"
export HEADROOM_PORT="${HEADROOM_PORT:-8787}"
export HEADROOM_PROXY_URL="http://127.0.0.1:${HEADROOM_PORT}"
path_prepend "${HEADROOM_HOME}/.venv/bin"
```

- [ ] **Step 2: Add small wrapper functions for the common Headroom workflows**

```sh
headroom-proxy() {
  (cd "${HEADROOM_HOME}" && headroom proxy --port "${HEADROOM_PORT}")
}

headroom-doctor() {
  (cd "${HEADROOM_HOME}" && headroom doctor --port "${HEADROOM_PORT}" "$@")
}

headroom-codex() {
  (cd "${HEADROOM_HOME}" && ANTHROPIC_BASE_URL="${HEADROOM_PROXY_URL}" OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1" headroom wrap codex "$@")
}

headroom-claude() {
  (cd "${HEADROOM_HOME}" && ANTHROPIC_BASE_URL="${HEADROOM_PROXY_URL}" OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1" headroom wrap claude "$@")
}
```

- [ ] **Step 3: Reload the shell and confirm the helpers are defined**

Run:
```sh
source clients/dotfiles/shell_common.sh
type headroom-proxy headroom-doctor headroom-codex headroom-claude
```
Expected: each helper resolves to a shell function.

### Task 2: Make the Codex MCP server independent of PATH

**Files:**
- Modify: `clients/codex/config.toml`

- [ ] **Step 1: Point the Headroom MCP command at the repo-local binary**

```toml
[mcp_servers.headroom]
command = "/Users/visualval/.local/share/prompthub/headroom/.venv/bin/headroom"
args = ["mcp", "serve"]
```

- [ ] **Step 2: Confirm the config points at the exact binary in the Headroom venv**

Run:
```sh
rg -n 'mcp_servers.headroom|command = "/Users/visualval/.local/share/prompthub/headroom/.venv/bin/headroom"' clients/codex/config.toml
```
Expected: the Headroom block is present and uses the explicit repo-local path.

### Task 3: Record the user-visible change and verify runtime state

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add an Unreleased changelog entry**

```md
- **Headroom shell wiring**: Added repo-local Headroom shell helpers in `clients/dotfiles/shell_common.sh` (`headroom-proxy`, `headroom-doctor`, `headroom-codex`, `headroom-claude`) and pointed the Codex MCP server at the repo-local Headroom binary so the proxy and MCP server start reliably from this workspace.
```

- [ ] **Step 2: Verify the proxy health check**

Run:
```sh
headroom-doctor
```
Expected: `proxy` passes when the proxy is already running, and the shell helpers are usable from the current shell.

