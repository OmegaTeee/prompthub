# PromptHub Quick Start

Welcome to PromptHub. This guide walks you through setup and your first test. You will be up and running in about five minutes.

## What Is PromptHub?

PromptHub is a central hub that connects your apps to AI models. Think of it like a power strip for AI: you plug all your tools into one place, and PromptHub handles the wiring.

With PromptHub you can:

- Use AI features in multiple apps from a single endpoint.
- Improve your prompts automatically for better results.
- Remember important information across conversations.
- Save money by running AI locally when possible.

## Before You Start

Make sure you have these three things ready:

1. **PromptHub installed** on your Mac.
2. **Ollama running** for local AI features. Launch it from your Applications folder or run `ollama serve` in Terminal.
3. **An internet connection** if you plan to use cloud features like the Claude API.

## Getting Started

### Step 1: Launch PromptHub

PromptHub can start automatically at login. To check or enable this:

1. Open **System Preferences > General > Login Items & Extensions**.
2. Look for **PromptHub** in the list.
3. If it is missing, click the **+** button and add PromptHub.

To start it by hand from Terminal, run these commands:

```bash
cd ~/prompthub
source .venv/bin/activate
uvicorn router.main:app --host 127.0.0.1 --port 9090
```

### Step 2: Open the Dashboard

Once PromptHub is running, open your browser and go to:

```
http://localhost:9090
```

You will see the PromptHub Dashboard. It has three main areas:

- **Status panel** -- shows whether all systems are working.
- **Memory stats** -- displays how much information is stored.
- **Recent sessions** -- lists your latest conversations.

### Step 3: Connect Your Apps

PromptHub works with apps that support MCP (Model Context Protocol). MCP is a standard way for apps to talk to AI servers -- like USB but for AI tools.

Popular supported apps include:

- Claude for Mac
- VS Code (with extensions)
- Raycast
- Custom tools

Each app needs a small config change. See the **App Configuration** section below for details.

**Key points:**

- PromptHub runs on `localhost:9090`.
- The dashboard gives you a quick health overview.
- Each app needs a one-time config change to connect.

## Dashboard Overview

The dashboard gives you a bird's-eye view of the whole system.

| Section      | What It Shows                                              |
| ------------ | ---------------------------------------------------------- |
| **Status**   | Green = all systems running. Red = something needs fixing. |
| **Memory**   | Active sessions, stored facts, and memory blocks.          |
| **Sessions** | Recent conversations with timestamps.                      |

### Checking System Health

Click the **Health Check** button on the dashboard. It verifies four things:

1. The router is running.
2. Ollama is responding.
3. The database is accessible.
4. API keys are loaded.

If any check fails, the dashboard tells you which one so you know where to look.

## Your First Test

Before connecting apps, confirm that PromptHub itself is healthy. This is like turning the key to make sure the engine starts before you drive.

1. Open Terminal.
2. Run this command:

   ```bash
   curl -s http://localhost:9090/health | python3 -m json.tool
   ```

3. Look for `"status": "healthy"` in the output.

If you see that response, PromptHub is ready to go.

**Key points:**

- The `/health` endpoint is the fastest way to check if PromptHub is running.
- A healthy response means the router, Ollama, and database are all working.

## What to Do Next

Now that PromptHub is running, pick your next step:

- **Enable Prompt Enhancement** -- See the *Prompt Enhancement Guide* to get better AI responses automatically.
- **Set Up Sessions** -- See the *Session Memory Guide* to let PromptHub remember context across conversations.
- **Connect Your Apps** -- See the *App Configuration Guide* for per-app setup instructions.
- **Troubleshoot Issues** -- See the *Troubleshooting Guide* if something is not working.

## Getting Help

If something goes wrong, follow these steps in order:

1. Click **Health Check** in the dashboard to see which component failed.
2. Read the **Troubleshooting Guide** in this docs folder.
3. Check the log file for error details:

   ```bash
   tail -f ~/prompthub/logs/router-stderr.log
   ```

---

You are now ready to use PromptHub. Start with one app, get comfortable, and add more over time.
