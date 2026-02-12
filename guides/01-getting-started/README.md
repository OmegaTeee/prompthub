# Getting Started with AgentHub

**Start here if you're new to AgentHub!**

This section covers everything you need to install and verify AgentHub on your macOS system.

---

## Choose Your Installation Path

### 🚀 [Quick Start](quick-start.md)
**For experienced developers**

- Commands only, minimal explanation
- Assumes familiarity with Terminal, Python, Node.js
- 10-minute installation
- **Best for:** Developers, engineers, DevOps

[→ Start Quick Installation](quick-start.md)

---

### 📚 [Detailed Installation](detailed-installation.md)
**For beginners and non-programmers**

- Step-by-step with full explanations
- Explains what each command does and why
- 30-45 minute installation
- **Best for:** First-time users, non-technical users

[→ Start Detailed Installation](detailed-installation.md)

---

### ✅ [Verification Guide](verification.md)
**After installation (all users)**

- Comprehensive testing procedures
- Health checks for all components
- Troubleshooting common issues
- Daily usage patterns
- **Best for:** Post-install verification, troubleshooting

[→ Verify Your Installation](verification.md)

---

## Which Path Should I Choose?

| Your Experience | Recommended Path | Time |
|-----------------|------------------|------|
| I'm comfortable with Terminal | [Quick Start](quick-start.md) | 10 min |
| I've never used Terminal | [Detailed Installation](detailed-installation.md) | 30-45 min |
| I just installed AgentHub | [Verification Guide](verification.md) | 5-15 min |
| Something isn't working | [Verification Guide](verification.md) → Troubleshooting | 5-15 min |

---

## What You'll Install

All paths install the same components:

1. **Prerequisites**
   - Homebrew (macOS package manager)
   - Python 3.11+ (runtime for AgentHub)
   - Node.js 20+ (runtime for MCP servers)

2. **AgentHub Core**
   - Router software (FastAPI server)
   - MCP servers (filesystem, fetch, brave-search, etc.)
   - Configuration files

3. **AI Models (Optional but Recommended)**
   - Ollama (local AI model runner)
   - Models: llama3.2, deepseek-r1, qwen2.5-coder

4. **Auto-Start (Optional)**
   - LaunchAgent for automatic startup

5. **Client Configuration**
   - Connect Claude Desktop, VS Code, or Raycast

---

## System Requirements

### Minimum
- macOS 11 (Big Sur) or later
- 8GB RAM
- 10GB free disk space (without models)
- Intel or Apple Silicon (M1/M2/M3)

### Recommended
- macOS 13 (Ventura) or later
- 16GB RAM
- 30GB free disk space (with AI models)
- Apple Silicon (M1/M2/M3)

---

## Before You Start

### Have These Ready
- [ ] Mac with administrator access
- [ ] Internet connection (for downloads)
- [ ] At least one AI client installed:
  - [Claude Desktop](https://claude.ai/download)
  - [VS Code](https://code.visualstudio.com)
  - [Raycast](https://raycast.com)

### Optional: Gather API Keys
If you plan to use these services, have API keys ready:
- Brave Search API (for web search)
- OpenAI API (if using OpenAI mode)
- Other service credentials

**Don't have keys yet?** That's fine — you can add them later. AgentHub works without them.

---

## What's Next?

After completing installation and verification:

### Core Setup (Recommended)
- [LaunchAgent Setup](../02-core-setup/launchagent.md) - Auto-start on login
- [Keychain Setup](../02-core-setup/keychain.md) - Secure credential storage
- [Docker Setup](../02-core-setup/docker.md) - Alternative deployment

### Connect More Apps
- [Claude Desktop](../03-integrations/claude-desktop.md) - Research & content
- [VS Code](../03-integrations/vscode.md) - Software development
- [Raycast](../03-integrations/raycast.md) - Quick commands

### Learn Workflows
- [Code Development](../04-workflows/code-development.md) - VS Code workflow
- [Content Creation](../04-workflows/content-creation.md) - Writing workflow
- [Quick Commands](../04-workflows/quick-commands.md) - Raycast workflow

---

## Getting Help

### If You Get Stuck
1. **Check [Verification Guide](verification.md)** - Troubleshooting section
2. **See [Common Issues](../_shared/troubleshooting-common.md)** - Centralized troubleshooting
3. **Review [Health Checks](../_shared/health-checks.md)** - Diagnostic procedures
4. **Check [Terminology](../_shared/terminology.md)** - Understand the terms

### Common Questions

**Q: Do I need programming experience?**
A: No! The [Detailed Installation](detailed-installation.md) guide is written for non-programmers.

**Q: How long does installation take?**
A: 10 minutes (Quick Start) or 30-45 minutes (Detailed Installation)

**Q: Can I use multiple AI clients?**
A: Yes! Connect Claude Desktop, VS Code, Raycast, and more to the same AgentHub.

**Q: Do I need to pay for API keys?**
A: No. AgentHub works with local models (free). API keys are optional for services like Brave Search.

**Q: Will this slow down my Mac?**
A: No. AgentHub uses < 200MB RAM without models, ~500MB with models.

---

## Installation Overview

### Quick Path (10 minutes)

```
Install Prerequisites (5 min)
     ↓
Install AgentHub (3 min)
     ↓
Verify Installation (2 min)
     ↓
Done! ✅
```

### Detailed Path (30-45 minutes)

```
Phase 1: Install Prerequisites (10 min)
     ↓
Phase 2: Install AgentHub (10 min)
     ↓
Phase 3: Install Ollama & Models (10 min)
     ↓
Phase 4: Start AgentHub (5 min)
     ↓
Phase 5: Auto-Start Setup (5 min - optional)
     ↓
Phase 6: Connect Apps (10 min)
     ↓
Done! ✅
```

---

## Success Checklist

After installation, you should be able to:

- [ ] Run `curl http://localhost:9090/health` and get healthy status
- [ ] Open dashboard at `http://localhost:9090/dashboard`
- [ ] See at least one client connected
- [ ] Ask a question in your AI client and get a response
- [ ] (Optional) AgentHub starts automatically after Mac restart

If all checked, installation is successful! ✅

---

**Estimated Total Time:** 10-45 minutes (depending on path)
**Difficulty:** Beginner to Intermediate
**Prerequisites:** macOS 11+, Administrator access
