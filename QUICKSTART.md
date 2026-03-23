# PromptHub Quickstart

Get PromptHub running and connected to your first app. This takes about five minutes.

PromptHub is a local hub that connects your AI-powered apps to Ollama models through one endpoint. Think of it like a power strip: you plug all your tools into one place, and PromptHub handles the wiring.

---

## 1. Prerequisites

You need four things installed on your Mac before you start:

1. **Homebrew** — the macOS package manager. If you do not have it, visit [brew.sh](https://brew.sh).
2. **Ollama** — runs AI models locally. Install it from [ollama.com](https://ollama.com), then pull a model:
   ```bash
   ollama pull gemma3:4b
   ```
3. **Node.js** — needed for the MCP bridge:
   ```bash
   brew install node
   ```
4. **Python 3.11+** — via `pyenv` or system Python.

---

## 2. Project Layout

```text
~/prompthub/
├── app/              # FastAPI router + CLI (Python)
├── scripts/          # prompthub-start.zsh, prompthub-kill.zsh, open-webui/, etc.
├── mcps/             # MCP bridge + client configs (Node)
├── docs/             # Developer docs, ADRs, and user guides
└── logs/             # Router logs
```

Router code and Python dependencies live under `app/`. The MCP bridge and Claude configs live under `mcps/`.

---

## 3. One-Time Setup

Run these commands once to create the Python environment:

1. Open Terminal.
2. Navigate to the project:
   ```bash
   cd ~/prompthub/app
   ```
3. Create and populate the virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```
4. Make the helper scripts executable:
   ```bash
   chmod +x ~/prompthub/scripts/prompthub-start.zsh ~/prompthub/scripts/prompthub-kill.zsh
   ```

**Key points:**
- You only need to do this once.
- The virtual environment keeps PromptHub's dependencies separate from the rest of your system.

---

## 4. Start PromptHub

Run the start script:

```bash
~/prompthub/scripts/prompthub-start.zsh
```

The script does four things for you:

1. Starts Ollama if it is not already running.
2. Activates the Python virtual environment.
3. Launches the router on `http://127.0.0.1:9090`.
4. Runs a health check and lists your available models.

Watch the Terminal output. You should see a successful health check and a model list. If either fails, fix the error before moving on.

Logs are written to:
- `logs/router-stdout.log`
- `logs/router-stderr.log`

**Key points:**
- One command starts everything.
- Always check the health output before opening your apps.

---

## 5. Connect Claude Desktop

Claude Desktop talks to PromptHub through a Node MCP bridge. MCP (Model Context Protocol) is a standard way for apps to talk to AI servers.

### Where the config lives

The Claude MCP config is at:

```text
~/prompthub/mcps/configs/claude-desktop.json
```

It tells Claude to launch a bridge that connects to PromptHub with these settings:

| Setting | Value |
|---------|-------|
| PromptHub URL | `http://127.0.0.1:9090` |
| API Key | `sk-prompthub-claude-desktop-001` |
| Servers | sequential-thinking, desktop-commander, context7 |

You can regenerate or validate this config with the CLI:

```bash
cd ~/prompthub/app
python -m cli generate claude-desktop
python -m cli validate claude-desktop
```

### Usage

1. Start PromptHub (section 4 above).
2. Wait for the health check to pass.
3. Open Claude Desktop.
4. In Claude's MCP settings, confirm `prompthub-bridge` is enabled.
5. Start a conversation. You should see tools like `desktop-commander_*`, `context7_*`, and `sequential-thinking_*`.

### If tools are missing or Claude hangs

Check the bridge log:

```bash
tail -n 40 ~/prompthub/mcps/configs/claude-desktop--prompthub-bridge.log
```

If you see `Failed to fetch server list from router: fetch failed`, the router was not running when Claude started. Restart:

```bash
~/prompthub/scripts/prompthub-kill.zsh
~/prompthub/scripts/prompthub-start.zsh
```

Then reopen Claude Desktop.

**Key points:**
- Start PromptHub before opening Claude.
- The bridge log tells you exactly what went wrong.

---

## 6. Connect OpenAI-Compatible Apps

Any app that supports the OpenAI API can talk to PromptHub. This includes VS Code, Raycast, Cursor, and custom scripts.

### Find your API key

Keys live in:

```text
~/prompthub/app/configs/api-keys.json
```

Example entry:

```json
{
  "keys": {
    "sk-prompthub-code-001": {
      "client_name": "vscode",
      "enhance": false,
      "description": "VS Code (pass-through)"
    }
  }
}
```

### VS Code setup

Add this to your VS Code `settings.json`:

```jsonc
{
  "chat.models": [
    {
      "id": "gemma3:27b",
      "provider": "openaiCompatible",
      "url": "http://localhost:9090/v1",
      "apiKey": "sk-prompthub-code-001"
    }
  ]
}
```

Then select the model in the chat panel.

### Quick test

Confirm the API works from Terminal:

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-code-001" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "messages": [
      {"role": "user", "content": "Hello from PromptHub!"}
    ]
  }'
```

**Key points:**
- Any OpenAI-compatible app needs three things: URL, API key, and model name.
- Test from Terminal first to confirm things work.

---

## 7. Stop and Restart

To stop the router and MCP bridge:

```bash
~/prompthub/scripts/prompthub-kill.zsh
```

This stops PromptHub but leaves Ollama running. To stop Ollama too:

```bash
killall ollama
```

To restart from scratch:

```bash
~/prompthub/scripts/prompthub-kill.zsh
~/prompthub/scripts/prompthub-start.zsh
```

---

## 8. Next Steps

- **More app examples** — See `docs/guides/04-openai-api-guide.md` for Python scripts, Raycast, and other clients.
- **Run diagnostics** — From `~/prompthub/app`, run `python -m cli diagnose` to check all systems.
- **Browse user guides** — Open `~/prompthub/docs/guides/` for the full set.
- **Explore internals** — See `~/prompthub/docs/` for architecture decisions and developer docs.
