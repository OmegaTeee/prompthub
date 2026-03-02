# PromptHub Quick Start

Welcome to PromptHub! This guide will help you get up and running in just a few minutes.

## What is PromptHub?

PromptHub is a smart assistant hub that connects all your favorite apps to AI models. It works like a central control panel, allowing you to:
- Use AI features in multiple apps from one place
- Automatically improve your prompts for better results
- Remember important information across conversations
- Save money by using local AI when possible

## Prerequisites

Before starting, make sure you have:
- PromptHub installed on your Mac
- Ollama running (for local AI features) — you can start it from your applications or terminal
- An internet connection (for cloud-based features like Claude API)

## Getting Started in 3 Steps

### Step 1: Launch PromptHub

PromptHub starts automatically when you log in. To manually start it:

1. Open **System Preferences > General > Login Items & Extensions**
2. Look for **PromptHub** in the "Allow in the next section" list
3. If not there, add it by clicking the **+** button and selecting PromptHub

You can also start it manually from the terminal:
```
cd ~/.local/share/prompthub
source .venv/bin/activate
uvicorn router.main:app --host 127.0.0.1 --port 9090
```

### Step 2: Access the Dashboard

Once PromptHub is running, open your web browser and go to:
```
http://localhost:9090
```

You should see the PromptHub Dashboard with:
- **Status panel** — Shows if all systems are working
- **Memory stats** — Displays stored information
- **Recent sessions** — Lists your recent conversations

### Step 3: Connect Your Apps

PromptHub works with apps that support MCP (Model Context Protocol). Popular apps include:
- Claude for Mac
- VS Code (with extensions)
- Raycast
- Custom tools

Each app needs a small configuration change. See **App Configuration** section below.

## Dashboard Overview

The PromptHub dashboard shows:

| Section      | What it shows                                                       |
| ------------ | ------------------------------------------------------------------- |
| **Status**   | ✅ Green = all systems running, 🔴 Red = something needs attention |
| **Memory**   | Number of active sessions, facts stored, and memory blocks          |
| **Sessions** | List of your recent conversations with timestamps                   |

### Checking System Health

Click the **Health Check** button to verify:
- ✅ Router is running
- ✅ Ollama is responding
- ✅ Database is accessible
- ✅ API keys are loaded

## First Test

To verify everything works:

1. Open Terminal
2. Run this command to test the API:

   ```bash
   curl -s http://localhost:9090/health | python3 -m json.tool
   ```
3. You should see `"status": "healthy"`

## What's Next?

- **Enable Prompt Enhancement** — See *Prompt Enhancement Guide*
- **Set Up Sessions** — See *Session Memory Guide*
- **Connect Your Apps** — See *App Configuration Guide*
- **Troubleshoot Issues** — See *Troubleshooting Guide*

## Getting Help

If something isn't working:
1. Check the **Health Check** in the dashboard
2. Look at the **Troubleshooting Guide** in this docs folder
3. Check the logs at `~/.local/share/prompthub/logs/router-stderr.log`

---

**That's it!** You're now ready to use PromptHub. Start with one app and add more as you get comfortable.
