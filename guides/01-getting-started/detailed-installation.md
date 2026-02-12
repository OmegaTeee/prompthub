# Detailed Installation Guide

**For users new to Terminal and command-line tools**

> **What you'll learn:** Step-by-step installation with explanations of what each command does and why it's needed

---

## Welcome!

You're about to install AgentHub — a central hub that connects all your AI tools (Claude Desktop, VS Code, Raycast) and makes them work better together.

**Good news:** You don't need programming experience. This guide explains everything.

**Setup time:** 30-45 minutes (first time)

---

## Before You Start

### What You'll Need

- ✅ **Mac computer** (M1/M2/M3 or Intel, both work)
- ✅ **8GB RAM** (to run AI models)
- ✅ **20GB free disk space** (for software and models)
- ✅ **Administrator access** (you can install software)
- ✅ **At least one AI client** installed:
  - Claude Desktop ([claude.ai/download](https://claude.ai/download))
  - VS Code ([code.visualstudio.com](https://code.visualstudio.com))
  - Raycast ([raycast.com](https://raycast.com))

### What We're Installing

1. **Homebrew** - macOS package manager (app installer)
2. **Python 3.11** - Programming language AgentHub runs on
3. **Node.js 20** - JavaScript runtime for MCP servers
4. **Ollama** - Local AI models for prompt enhancement
5. **AgentHub** - The router software itself

---

## Phase 1: Install Prerequisites (10 minutes)

### Step 1: Open Terminal

**What is Terminal?**
Terminal is a text-based way to control your Mac. Don't worry — you'll just copy and paste commands.

**How to open:**
1. Press `Cmd + Space` (opens Spotlight)
2. Type "Terminal"
3. Press `Enter`

You'll see a window with a command prompt like this:

```
username@MacBook-Pro ~ %
```

This is where you'll paste commands.

---

### Step 2: Install Homebrew

**What is Homebrew?**
Think of it like the App Store, but for developer tools. It makes installing software much easier.

**Copy and paste this command:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**What's happening:**
- `curl` downloads the Homebrew installer
- `/bin/bash -c` runs the installer
- You'll be asked to press `Enter` to continue
- You may need to enter your Mac password (nothing will show when you type — that's normal!)

**This takes:** 2-3 minutes

**Expected output:**

```
==> Installation successful!
```

---

### Step 3: Install Python

**What is Python?**
Python is a programming language. AgentHub is written in Python, so we need it to run the software.

**Copy and paste this command:**

```bash
brew install python@3.11
```

**What's happening:**
- Homebrew downloads Python version 3.11
- Installs it in the correct location
- Sets up necessary system links

**This takes:** 3-5 minutes

**Verify it worked:**

```bash
python3 --version
```

**Expected output:**

```
Python 3.11.x
```

If you see this, Python is installed correctly! ✅

---

### Step 4: Install Node.js

**What is Node.js?**
Node.js runs JavaScript code. AgentHub's MCP servers (the tools it connects to) use Node.js.

**Copy and paste this command:**

```bash
brew install node@20
```

**This takes:** 3-5 minutes

**Verify it worked:**

```bash
node --version
```

**Expected output:**

```
v20.x.x
```

If you see a version number starting with 20, Node.js is installed correctly! ✅

---

## Phase 2: Install AgentHub (10 minutes)

### Step 1: Download AgentHub

**Option A: If you have the download file**
1. Open Finder
2. Navigate to your Downloads folder
3. Find `agenthub.zip` or `agenthub-*.tar.gz`
4. Double-click to extract it

**Option B: If using git (advanced)**

```bash
cd ~/.local/share
git clone https://github.com/YOUR_ORG/agenthub.git
```

For this guide, we'll assume you extracted to Downloads. Let's move it to the right place:

```bash
# Create the directory where AgentHub will live
mkdir -p ~/.local/share

# Move AgentHub there
mv ~/Downloads/agenthub ~/.local/share/

# Verify it's there
ls ~/.local/share/agenthub
```

**Expected output:**
You should see files like: `router/`, `mcps/`, `requirements.txt`, `.env.example`

---

### Step 2: Navigate to AgentHub Directory

**What does "navigate" mean?**
In Terminal, you're always "in" a directory (folder). We need to move into the AgentHub folder.

```bash
cd ~/.local/share/agenthub
```

**What this means:**
- `cd` = "change directory"
- `~` = your home folder (e.g., `/Users/yourname`)
- `.local/share/agenthub` = the path to AgentHub

**Verify you're in the right place:**

```bash
pwd
```

**Expected output:**

```
/Users/yourname/.local/share/agenthub
```

---

### Step 3: Set Up Python Environment

**What is a virtual environment?**
It's an isolated space for Python packages. This prevents conflicts with other Python software on your Mac.

```bash
# Create virtual environment
python3 -m venv .venv
```

**What's happening:**
- `python3 -m venv` creates a virtual environment
- `.venv` is the name of the folder it creates (you'll see a new `.venv/` folder)

**This takes:** 10-20 seconds

Now activate it:

```bash
source .venv/bin/activate
```

**What's happening:**
- `source` runs a script
- `.venv/bin/activate` activates the virtual environment
- Your prompt will change to show `(.venv)` at the beginning

**Your prompt should now look like:**

```
(.venv) username@MacBook-Pro agenthub %
```

The `(.venv)` means the environment is active! ✅

---

### Step 4: Install Python Dependencies

**What are dependencies?**
Libraries (code packages) that AgentHub needs to run. Think of them like ingredients for a recipe.

```bash
pip install -r requirements.txt
```

**What's happening:**
- `pip` is Python's package installer
- `install -r requirements.txt` installs all packages listed in the file
- You'll see lots of text scrolling by — that's normal!

**This takes:** 2-5 minutes

**Expected output (at the end):**

```
Successfully installed fastapi-... uvicorn-... structlog-... (and many others)
```

---

### Step 5: Install MCP Server Packages

**What are MCP servers?**
Tools that AgentHub connects to:
- `filesystem` - Read/write files
- `fetch` - Get content from websites
- `brave-search` - Search the web

```bash
# Navigate to MCP directory
cd mcps

# Install Node.js packages
npm install

# Go back to main directory
cd ..
```

**What's happening:**
- `npm install` reads `package.json` and installs all listed packages
- This downloads MCP server code from npm (Node's package registry)

**This takes:** 2-3 minutes

**Expected output:**

```
added XXX packages in Xs
```

---

### Step 6: Configure Environment Variables

**What are environment variables?**
Settings that AgentHub uses to know how to run. Think of them like preferences.

```bash
# Copy the example configuration
cp .env.example .env
```

**What's happening:**
- `cp` = copy
- `.env.example` = template file with example settings
- `.env` = the file AgentHub actually reads

Now let's edit it. We'll use a simple text editor:

```bash
nano .env
```

**You'll see the file contents.** The important settings are:

```bash
# Server configuration
HOST=0.0.0.0         # Listen on all network interfaces
PORT=9090            # Port number (don't change unless you have conflicts)

# Ollama configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434    # Default Ollama port

# Models
OLLAMA_MODEL=llama3.2  # Default model

# Logging
LOG_LEVEL=INFO        # INFO, DEBUG, WARNING, ERROR
```

**For now, don't change anything.** The defaults work for most people.

**To save and exit nano:**
1. Press `Ctrl + X`
2. Press `Y` (to confirm save)
3. Press `Enter`

---

## Phase 3: Install Ollama (10 minutes)

**What is Ollama?**
Ollama runs AI models locally on your Mac. AgentHub uses these to improve prompts before sending them to your AI clients.

### Step 1: Install Ollama

```bash
brew install ollama
```

**This takes:** 2-3 minutes

---

### Step 2: Start Ollama Service

```bash
brew services start ollama
```

**What's happening:**
- Ollama starts as a background service
- It will automatically start when you restart your Mac

**Verify it's running:**

```bash
curl http://localhost:11434/api/version
```

**Expected output:**

```json
{"version":"0.1.20"}
```

If you see a version number, Ollama is running! ✅

---

### Step 3: Download AI Models

**What are AI models?**
Pre-trained artificial intelligence that processes text. We'll download three:
- `llama3.2` - Fast, general-purpose (for Raycast)
- `deepseek-r1:7b` - Structured reasoning (for Claude Desktop)
- `qwen2.5-coder:7b` - Code-focused (for VS Code)

```bash
# Download models (this is slow the first time)
ollama pull llama3.2
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
```

**This takes:** 10-20 minutes (models are large files, 4-7GB each)

You'll see progress bars like:

```
pulling manifest
pulling 6f4e2e0e2... 100% ▕███████████████▏ 4.7 GB
```

**Verify they downloaded:**

```bash
ollama list
```

**Expected output:**

```
NAME                    SIZE
llama3.2:latest        2.0 GB
deepseek-r1:7b         4.1 GB
qwen2.5-coder:7b       4.7 GB
```

---

## Phase 4: Start AgentHub (5 minutes)

Now we're ready to start AgentHub for the first time!

### Step 1: Navigate to AgentHub Directory (if not already there)

```bash
cd ~/.local/share/agenthub
source .venv/bin/activate
```

Remember, `(.venv)` should appear in your prompt.

---

### Step 2: Start the Server

```bash
uvicorn router.main:app --host 0.0.0.0 --port 9090
```

**What's happening:**
- `uvicorn` is the web server that runs AgentHub
- `router.main:app` tells it where the AgentHub code is
- `--host 0.0.0.0` makes it accessible from any network interface
- `--port 9090` sets the port number

**Expected output:**

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9090
```

**If you see this, AgentHub is running!** ✅

**Important:** Leave this Terminal window open. AgentHub will stop if you close it (for now — we'll fix this in Phase 5).

---

### Step 3: Verify It's Working

Open a **new Terminal window** (Cmd + N) and test:

```bash
curl http://localhost:9090/health
```

**Expected output:**

```json
{"status":"healthy","timestamp":"2026-02-05T10:30:00Z","version":"0.1.0"}
```

**Success!** AgentHub is responding! ✅

---

### Step 4: View the Dashboard

Open your web browser and go to:

```
http://localhost:9090/dashboard
```

**You should see:**
- AgentHub monitoring dashboard
- List of MCP servers (filesystem, fetch, etc.)
- Activity log (empty for now)
- Circuit breaker status

If you see the dashboard, everything is working correctly! ✅

---

## Phase 5: Auto-Start Setup (Optional but Recommended)

**The problem:** Right now, AgentHub only runs while that Terminal window is open. If you close it or restart your Mac, AgentHub stops.

**The solution:** Create a LaunchAgent that starts AgentHub automatically when you log in.

### Step 1: Create LaunchAgent Configuration

**What is a LaunchAgent?**
A macOS system file that tells your Mac to run a program automatically.

**Copy and paste this entire block:**

```bash
cat > ~/Library/LaunchAgents/com.agenthub.router.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agenthub.router</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ~/.local/share/agenthub && source .venv/bin/activate && uvicorn router.main:app --host 0.0.0.0 --port 9090</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>~/Library/Logs/agenthub-router.log</string>
    <key>StandardErrorPath</key>
    <string>~/Library/Logs/agenthub-router-error.log</string>
</dict>
</plist>
EOF
```

**What this does:**
- Creates a file at `~/Library/LaunchAgents/com.agenthub.router.plist`
- Tells macOS how to run AgentHub
- Configures it to start on login (`RunAtLoad`)
- Keeps it running (`KeepAlive`)
- Saves logs for troubleshooting

---

### Step 2: Load the LaunchAgent

```bash
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

**What's happening:**
- `launchctl` is macOS's service manager
- `load` tells it to register and start the service

**Verify it's running:**

```bash
launchctl list | grep com.agenthub.router
```

**Expected output:**

```
12345  0  com.agenthub.router
```

The first number is the process ID (PID). If you see this, the service is running! ✅

---

### Step 3: Test Auto-Start

Now you can close the Terminal window where you manually started AgentHub. The LaunchAgent will keep it running.

**Test the health endpoint again:**

```bash
curl http://localhost:9090/health
```

**Expected output:**

```json
{"status":"healthy"...}
```

**Perfect!** AgentHub now starts automatically and runs in the background. ✅

---

## Phase 6: Connect Your Apps (10 minutes)

Now let's connect your AI clients to AgentHub.

**Choose one to start with** (you can add more later):
- Claude Desktop
- VS Code
- Raycast

---

### Option A: Claude Desktop

**Step 1:** Open Claude Desktop config

```bash
# Edit config file
open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Step 2:** Replace the contents with:

```json
{
  "mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Enhance": "true",
        "X-Client-Name": "claude-desktop"
      }
    }
  }
}
```

**What this does:**
- Tells Claude Desktop to connect to AgentHub at `localhost:9090`
- `X-Enhance: true` enables prompt enhancement
- `X-Client-Name: claude-desktop` identifies this client

**Step 3:** Save the file (Cmd + S) and close TextEdit

**Step 4:** Restart Claude Desktop
1. Quit Claude Desktop completely (Cmd + Q)
2. Open it again

**Step 5:** Verify connection

In Claude Desktop, ask:

```
Am I connected to AgentHub?
```

You should get a response confirming the connection! ✅

---

### Option B: VS Code

**Step 1:** Install Cline extension (if not already installed)
1. Open VS Code
2. Click Extensions icon (sidebar)
3. Search for "Cline"
4. Click "Install"

**Step 2:** Edit VS Code settings

```bash
code ~/.vscode/settings.json
```

**Step 3:** Add this configuration (merge with existing content):

```json
{
  "cline.mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Enhance": "true",
        "X-Client-Name": "vscode"
      }
    }
  }
}
```

**Step 4:** Restart VS Code

**Step 5:** Open Cline sidebar and verify you see "Connected to agenthub"

---

### Option C: Raycast

**Step 1:** Create Raycast config directory

```bash
mkdir -p ~/Library/Application\ Support/com.raycast.macos
```

**Step 2:** Create MCP servers config

```bash
cat > ~/Library/Application\ Support/com.raycast.macos/mcp_servers.json << 'EOF'
{
  "agenthub": {
    "url": "http://localhost:9090",
    "headers": {
      "X-Enhance": "true",
      "X-Client-Name": "raycast"
    }
  }
}
EOF
```

**Step 3:** Restart Raycast

```bash
killall Raycast
sleep 2
open -a Raycast
```

**Step 4:** Test by opening Raycast (Cmd + Space) and asking a question

---

## Success Checklist

Before you finish, verify everything works:

- [ ] `curl http://localhost:9090/health` returns healthy status
- [ ] Dashboard loads at `http://localhost:9090/dashboard`
- [ ] At least one client (Claude/VS Code/Raycast) is connected
- [ ] You can ask a question and get a response
- [ ] LaunchAgent is loaded: `launchctl list | grep agenthub`

If all are checked, setup is complete! ✅

---

## What's Next?

### Learn More
- [Verification Guide](verification.md) - Comprehensive testing
- [Core Setup](../02-core-setup/) - LaunchAgent, Keychain, Docker guides
- [Integrations](../03-integrations/) - Connect more apps
- [Workflows](../04-workflows/) - Practical usage patterns

### Get Help
- [Common Troubleshooting](../_shared/troubleshooting-common.md)
- [Health Checks](../_shared/health-checks.md)
- [Terminology](../_shared/terminology.md)

---

**Last Updated:** 2026-02-05
**Audience:** Beginners, non-programmers
**Time:** 30-45 minutes
**Difficulty:** Beginner (no prior experience needed)
