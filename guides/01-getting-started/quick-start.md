# Quick Start Guide

**For experienced developers who want to get AgentHub running in 10 minutes**

> **What you'll learn:** Minimal-explanation installation flow with commands only

---

## Prerequisites

- ✅ macOS (M1/M2/M3 or Intel)
- ✅ 8GB RAM, 20GB disk space
- ✅ Administrator access
- ✅ Familiar with Terminal

**Estimated time:** 10 minutes

---

## Installation

### 1. Install Dependencies

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Install Node.js 20
brew install node@20

# Verify versions
python3 --version  # Should be 3.11+
node --version     # Should be 20.x
```

---

### 2. Clone and Install AgentHub

```bash
# Clone repository (or navigate to downloaded source)
cd ~/.local/share
git clone https://github.com/YOUR_ORG/agenthub.git
# Or: tar -xzf agenthub-*.tar.gz

# Navigate to directory
cd agenthub

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install MCP server packages
cd mcps
npm install
cd ..
```

---

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your preferred editor)
nano .env
# Or: vim .env
# Or: code .env

# Minimum required settings:
# HOST=0.0.0.0
# PORT=9090
# OLLAMA_HOST=localhost
# OLLAMA_PORT=11434
```

---

### 4. Install Ollama (for enhancement)

```bash
# Install Ollama
brew install ollama

# Start Ollama service
brew services start ollama

# Pull required models
ollama pull llama3.2
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b

# Verify
ollama list
```

---

### 5. Start AgentHub

```bash
# Navigate to AgentHub directory
cd ~/.local/share/agenthub
source .venv/bin/activate

# Start server
uvicorn router.main:app --host 0.0.0.0 --port 9090
```

**Or use development mode with hot-reload:**

```bash
uvicorn router.main:app --reload --port 9090
```

---

### 6. Verify Installation

```bash
# In a new terminal:
curl http://localhost:9090/health

# Expected: {"status":"healthy","timestamp":"...","version":"0.1.0"}

# List MCP servers
curl http://localhost:9090/servers

# Check dashboard
open http://localhost:9090/dashboard
```

---

## Auto-Start Setup

### Create LaunchAgent (macOS)

```bash
# Create plist file
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

# Load LaunchAgent
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist

# Verify
launchctl list | grep com.agenthub.router
```

---

## Store Credentials (Optional)

```bash
# Example: Brave Search API key
security add-generic-password \
  -s "agenthub.brave_api_key" \
  -a "agenthub" \
  -w "YOUR_API_KEY_HERE"

# Example: OpenAI API key (if using OpenAI mode)
security add-generic-password \
  -s "agenthub.openai_api_key" \
  -a "agenthub" \
  -w "YOUR_OPENAI_KEY_HERE"

# Verify credentials stored
security find-generic-password -s "agenthub.brave_api_key" -w
```

---

## Client Configuration

### Claude Desktop

```bash
# Edit config
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Add:
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

---

### VS Code

```bash
# Edit settings
code ~/.vscode/settings.json

# Add (or merge):
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

---

### Raycast

```bash
# Create config directory
mkdir -p ~/Library/Application\ Support/com.raycast.macos

# Create MCP config
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

---

## Quick Reference

### Common Commands

```bash
# Start AgentHub manually
cd ~/.local/share/agenthub && source .venv/bin/activate && uvicorn router.main:app --port 9090

# Stop LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist

# Restart LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist

# View logs
tail -f ~/Library/Logs/agenthub-router.log
tail -f ~/Library/Logs/agenthub-router-error.log

# Health check
curl http://localhost:9090/health

# List servers
curl http://localhost:9090/servers

# Open dashboard
open http://localhost:9090/dashboard
```

---

## Troubleshooting Quick Fixes

### Connection refused

```bash
# Check if running
ps aux | grep "uvicorn router.main:app"

# Check port
lsof -i :9090

# Restart
launchctl restart com.agenthub.router
```

---

### Port conflict

```bash
# Find process using port 9090
lsof -i :9090

# Kill it (use with caution)
kill -9 <PID>

# Or change AgentHub port in .env
echo "PORT=9091" >> ~/.local/share/agenthub/.env
```

---

### Missing Python dependencies

```bash
cd ~/.local/share/agenthub
source .venv/bin/activate
pip install -r requirements.txt
```

---

### MCP servers not responding

```bash
# Reinstall MCP packages
cd ~/.local/share/agenthub/mcps
rm -rf node_modules package-lock.json
npm install
cd ..

# Restart AgentHub
launchctl restart com.agenthub.router
```

---

## Next Steps

**You're done!** AgentHub is now running and auto-starts on login.

**Explore:**
- [Detailed Installation Guide](detailed-installation.md) - If you need more explanation
- [Verification Guide](verification.md) - Comprehensive testing
- [Core Setup Guides](../02-core-setup/) - LaunchAgent, Keychain, Docker
- [Integration Guides](../03-integrations/) - Client-specific configurations
- [Workflows](../04-workflows/) - Practical usage patterns

**For issues:**
- [Common Troubleshooting](../_shared/troubleshooting-common.md)
- [Health Checks](../_shared/health-checks.md)

---

**Last Updated:** 2026-02-05
**Audience:** Experienced developers
**Time:** 10 minutes
**Difficulty:** Beginner (with Terminal experience)
