# PromptHub User Guides

**Complete guide to installing, configuring, and using PromptHub as your centralized MCP router**

## 🎯 Quick Start Path

**New to PromptHub?** Choose your path:

### Fast Track (10 minutes)
1. **[01-getting-started/quick-start](01-getting-started/quick-start.md)** → Commands-only installation
2. **[03-integrations/quick-config](03-integrations/quick-config.md)** → Copy-paste client configs
3. **[01-getting-started/verification](01-getting-started/verification.md)** → Quick health check

### Detailed Path (45 minutes)
1. **[01-getting-started/detailed-installation](01-getting-started/detailed-installation.md)** → Step-by-step with explanations
2. **[02-core-setup](02-core-setup/)** → Configure auto-start and credentials
3. **[03-integrations](03-integrations/)** → Connect your favorite apps
4. **[01-getting-started/verification](01-getting-started/verification.md)** → Comprehensive testing

**Choose based on your experience:**
- **Developers:** Fast Track (10 min)
- **First-time users:** Detailed Path (45 min)

---

## 📚 Guide Categories

### 01 - Getting Started
**Start here!** Installation and initial setup.

**Choose your path:**
- [Quick Start](01-getting-started/quick-start.md) - Commands only (10 min)
- [Detailed Installation](01-getting-started/detailed-installation.md) - Step-by-step (45 min)
- [Verification Guide](01-getting-started/verification.md) - Post-install testing (15 min)

[→ Browse Getting Started guides](01-getting-started/)

---

### 02 - Core Setup
**Essential configuration** for reliable operation.

**Essential:**
- [LaunchAgent](02-core-setup/launchagent.md) - Auto-start on login (10 min)
- [Keychain](02-core-setup/keychain.md) - Secure credentials (10 min)
- [Docker](02-core-setup/docker.md) - Container deployment (15 min)

**Advanced Features:**
- [Circuit Breaker](02-core-setup/circuit-breaker.md) - Resilience patterns (15 min)
- [Enhancement Rules](02-core-setup/enhancement-rules.md) - AI model configuration (15 min)
- [Audit Logging](02-core-setup/audit-logging.md) - Security & compliance (15 min)

[→ Browse Core Setup guides](02-core-setup/)

---

### 03 - Integrations
**Connect your apps** to PromptHub.

#### Primary Clients
- [Claude Desktop](03-integrations/claude-desktop.md) - Research & content creation
- [VS Code](03-integrations/vscode.md) - Software development
- [Raycast](03-integrations/raycast.md) - Quick commands & productivity

#### Specialized
- [Figma](03-integrations/figma.md) - Design-to-code workflows
- [ComfyUI](03-integrations/comfyui.md) - AI image generation

#### Reference
- [Quick Config](03-integrations/quick-config.md) - Copy-paste configs for all clients

[→ Browse Integration guides](03-integrations/)

---

### 04 - Workflows
**Practical usage patterns** and best practices.

**Real-world workflows:**
- [Code Development](04-workflows/code-development.md) - VS Code + Qwen3-Coder (15 min)
- [Content Creation](04-workflows/content-creation.md) - Claude Desktop + DeepSeek-R1 (15 min)
- [Quick Commands](04-workflows/quick-commands.md) - Raycast productivity (10 min)
- [Design to Code](04-workflows/design-to-code.md) - Figma integration (15 min)

[→ Browse Workflow guides](04-workflows/)

---

### 05 - Testing
**Validate and troubleshoot** your setup.

- [Integration Tests](05-testing/integration-tests.md) - Comprehensive test suite (30 min)

**Common Issues:** See [Shared Troubleshooting](_shared/troubleshooting-common.md)

**Health Checks:** See [Health Check Guide](_shared/health-checks.md)

[→ Browse Testing guides](05-testing/)

---

### 06 - Migration
**Upgrade guides** and migrations.

- [Keyring Migration](06-migration/keyring-migration.md) - Security CLI → Python keyring

[→ Browse Migration guides](06-migration/)

---

## 🗺️ Guide by Use Case

| I want to...                | Go to...                                                                | Time   |
| --------------------------- | ----------------------------------------------------------------------- | ------ |
| Install PromptHub (fast)     | [quick-start.md](01-getting-started/quick-start.md)                     | 10 min |
| Install PromptHub (detailed) | [detailed-installation.md](01-getting-started/detailed-installation.md) | 45 min |
| Verify my installation      | [verification.md](01-getting-started/verification.md)                   | 15 min |
| Connect Claude Desktop      | [claude-desktop.md](03-integrations/claude-desktop.md)                  | 10 min |
| Use with VS Code            | [vscode.md](03-integrations/vscode.md)                                  | 10 min |
| Use with Raycast            | [raycast.md](03-integrations/raycast.md)                                | 10 min |
| Set up auto-start           | [launchagent.md](02-core-setup/launchagent.md)                          | 10 min |
| Store API keys securely     | [keychain.md](02-core-setup/keychain.md)                                | 10 min |
| Understand circuit breaker  | [circuit-breaker.md](02-core-setup/circuit-breaker.md)                  | 15 min |
| Configure AI models         | [enhancement-rules.md](02-core-setup/enhancement-rules.md)              | 15 min |
| Enable audit logging        | [audit-logging.md](02-core-setup/audit-logging.md)                      | 15 min |
| Learn coding workflow       | [code-development.md](04-workflows/code-development.md)                 | 15 min |
| Learn writing workflow      | [content-creation.md](04-workflows/content-creation.md)                 | 15 min |
| Test my setup               | [integration-tests.md](05-testing/integration-tests.md)                 | 30 min |
| Run in Docker               | [docker.md](02-core-setup/docker.md)                                    | 15 min |
| Migrate credentials         | [keyring-migration.md](06-migration/keyring-migration.md)               | 10 min |
| Troubleshoot issues         | [troubleshooting-common.md](_shared/troubleshooting-common.md)          | 5 min  |

---

## 🎓 What is PromptHub?

PromptHub is a **centralized MCP (Model Context Protocol) router** for macOS that provides:

- **Unified Access** - Connect multiple apps (Claude Desktop, VS Code, Raycast) to 7+ MCP servers
- **Prompt Enhancement** - Automatically improve prompts with Ollama (DeepSeek-R1, Qwen3-Coder)
- **Auto-Restart** - MCP servers automatically restart on failure
- **Intelligent Caching** - Faster responses through in-memory cache
- **Audit Logging** - Production-grade request tracking

**Single endpoint:** `http://localhost:9090`

---

## 📖 Documentation Structure

```
guides/                          # USER-FACING (you are here)
├── README.md                    # This file
├── 01-getting-started/          # Installation
├── 02-core-setup/               # Essential config
├── 03-integrations/             # Client connections
├── 04-workflows/                # Usage patterns
├── 05-testing/                  # Validation
└── 06-migration/                # Upgrades

docs/                            # TECHNICAL/ENGINEERING
├── architecture/                # System design, ADRs
├── comparisons/                 # Technical comparisons
├── development/                 # Development guides
├── features/                    # Feature specs
└── reviews/                     # Code reviews
```

**Looking for technical documentation?** See [docs/DOCUMENTATION-INDEX.md](../docs/DOCUMENTATION-INDEX.md)

---

## 🆘 Getting Help

### Common Issues
- **Can't connect to PromptHub** → Check `curl http://localhost:9090/health`
- **MCP server not found** → Verify `configs/mcp-servers.json`
- **Credentials not working** → See [02-core-setup/keychain.md](02-core-setup/keychain.md)

### Comprehensive Testing
Run the full test suite: [05-testing/integration-tests.md](05-testing/integration-tests.md)

### Dashboard
View real-time status: `http://localhost:9090/dashboard`

---

## 🤝 Contributing

Found an issue or want to improve a guide?

1. **Report issues:** Document what you expected vs. what happened
2. **Suggest improvements:** What was confusing or missing?
3. **Share workflows:** How do you use PromptHub productively?

These guides are living documents that improve with user feedback!

---

**Last Updated:** 2026-02-06
**Guide Version:** 3.0.0 (Complete rewrite - Phase 1-6)
**PromptHub Version:** 0.1.0

### What's New in 3.0.0
- ✅ Split installation: Quick Start vs. Detailed paths
- ✅ Complete Section 04 Workflows (4 practical guides)
- ✅ Advanced features: Circuit Breaker, Enhancement Rules, Audit Logging
- ✅ Shared troubleshooting & health checks (eliminated duplication)
- ✅ Consistent style and terminology across all guides
- ✅ Comprehensive verification guide
