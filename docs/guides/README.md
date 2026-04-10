# PromptHub User Guides Index

Welcome! This folder contains everything you need to get the most out of PromptHub.

## What is PromptHub?

PromptHub is a local-first AI routing and enhancement system. It acts as a smart hub between your apps and your local language models (like those in LM Studio).

🚥 **_When no active rules are defined_:** PromptHub operates as a **simple bridge** — it passes prompts to your local LM Studio model with minimal transformation. It translates "OpenAI" → "LM Studio" but does *no* enhancement or routing.

🗺️ **_When active orchestration rules are applied_:**
PromptHub becomes an **orchestrated service mesh** — it enhances, modifies, and routes prompts based on defined rules (e.g., model selection, prompt templating, context filtering). It may:
- Choose different models based on input type
- Inject system prompts or formatting
- Apply safety checks or workflow steps
- Route to multiple local models dynamically

👉 **Key difference:**
- **_Bridge mode_** = passive translation, no intelligence
- **_Orchestration mode_** = active, intelligent routing and enhancement — PromptHub *decides* how and what to run

🔹 **Critical configuration note:**
PromptHub uses **local API secrets and model paths** (e.g., LM Studio model locations) even in bridge mode. These are stored securely and used to connect directly to your local models — meaning it’s not just a proxy, but a *configured local AI runtime* ready to run models without relying on external services.

✅ The name "Hub" reflects this evolution: from a simple bridge to an intelligent, rule-driven, locally configured AI workflow center.

## 📚 Start Here

### New Users
1. **[Quick Start Guide](01-quick-start-guide.md)** — Get PromptHub running in 3 steps (5 min read)
2. **[Why PromptHub? Comparison](07-why-prompthub-comparison.md)** — Understand what makes PromptHub different (10 min read)

### First Features to Try
1. **[Prompt Enhancement Guide](02-prompt-enhancement-user-guide.md)** — Automatically improve your prompts (8 min read)
2. **[Session Memory Guide](03-session-memory-guide.md)** — Remember information across conversations (10 min read)
3. **[OpenAI API Guide](04-openai-api-guide.md)** — Use PromptHub like an OpenAI-compatible server (10 min read)

---

## 🔧 Integration & Setup

### Connecting Your Apps
- **[Client Setup Guide](06-client-configuration-guide.md)** — MCP configs, AI providers, API keys, and enhancement rules for Claude, VS Code, Raycast, LM Studio, Open WebUI, and more (15 min read)
- **[API Integration Examples](../api/integration-examples.md)** — Python, Node.js, curl, Automator, Keyboard Maestro, Postman (developer reference)

Supported apps include:
- Claude Desktop / Claude Code
- VS Code / Cursor
- Raycast
- LM Studio
- Open WebUI
- Obsidian

---

## ❓ Troubleshooting

### Having Issues?
- **[Troubleshooting Guide](05-troubleshooting-guide.md)** — Common problems and solutions (20 min read)

Quick reference:
- Can't connect? → See "Cannot connect to localhost:9090"
- API errors? → See "401 Unauthorized"
- Too slow? → See "Request timed out"
- Database problems? → See "Database is locked"

---

## 🚀 Advanced Usage

### Power Users & Developers
- **[Advanced Power User Manual](08-advanced-power-user-manual.md)** — Custom configuration, monitoring, automation (30 min read)

Topics:
- Custom enhancement models
- Fine-grained API key management
- Performance tuning
- Debugging & logging
- Custom integrations

---

## Quick Navigation by Topic

### Prompt Enhancement
- Getting started: [Prompt Enhancement Guide](02-prompt-enhancement-user-guide.md)
- Troubleshooting slow enhancement: [Troubleshooting Guide](05-troubleshooting-guide.md#request-timed-out)
- Custom models: [Advanced Manual](08-advanced-power-user-manual.md#custom-enhancement-models)

### Session Memory & Context
- How it works: [Session Memory Guide](03-session-memory-guide.md)
- API examples: [Session Memory Guide — API](03-session-memory-guide.md#using-session-memory)
- Privacy: [Session Memory Guide — Privacy](03-session-memory-guide.md#privacy-and-data)

### Connecting Apps
- Overview: [App Configuration Guide](06-client-configuration-guide.md)
- Claude: [App Configuration — Claude](06-client-configuration-guide.md#claude-desktop)
- VS Code: [App Configuration — VS Code](06-client-configuration-guide.md#vs-code)
- Raycast: [App Configuration — Raycast](06-client-configuration-guide.md#raycast)
- Custom apps: [App Configuration — Generic Setup](06-client-configuration-guide.md#generic-http-client-setup)

### Using the API
- Overview: [OpenAI API Guide](04-openai-api-guide.md)
- Quick test: [OpenAI API — Quick Test](04-openai-api-guide.md#quick-test)
- API keys: [OpenAI API — API Keys](04-openai-api-guide.md#managing-api-keys)
- Troubleshooting: [OpenAI API — Troubleshooting](04-openai-api-guide.md#troubleshooting-api-issues)

### Troubleshooting
- Quick diagnosis: [Troubleshooting — Quick Diagnosis](05-troubleshooting-guide.md#quick-diagnosis)
- Common issues: [Troubleshooting — Common Issues](05-troubleshooting-guide.md#common-issues)
- Emergency help: [Troubleshooting — Getting Help](05-troubleshooting-guide.md#getting-more-help)

### Configuration & Customization
- Environment variables: [Advanced Manual — Environment Variables](08-advanced-power-user-manual.md#environment-variables)
- Enhancement rules: [Advanced Manual — Enhancement Rules](08-advanced-power-user-manual.md#custom-enhancement-rules)
- Performance tuning: [Advanced Manual — Performance Tuning](08-advanced-power-user-manual.md#performance-tuning)

---

## 📊 Reading Time by Role

### 👤 End User (Non-Technical)
**Total: ~40 minutes**
1. Quick Start Guide (5 min)
2. Why PromptHub (10 min)
3. One Feature Guide (10 min)
4. App Configuration (10 min)
5. Troubleshooting (5 min)

### 👨‍💻 Developer
**Total: ~60 minutes**
1. Quick Start (5 min)
2. All Feature Guides (30 min)
3. App Configuration (10 min)
4. Troubleshooting (10 min)
5. Advanced Manual (15 min)

### 🔧 System Administrator
**Total: ~90 minutes**
1. Quick Start (5 min)
2. Architecture overview (in main docs)
3. App Configuration (15 min)
4. Advanced Manual (30 min)
5. Troubleshooting (20 min)
6. Performance tuning (20 min)

---

## 🔍 Common Questions

**Q: Where do I start?**
A: [Quick Start Guide](01-quick-start-guide.md) — takes 5 minutes

**Q: How do I connect my app?**
A: [App Configuration Guide](06-client-configuration-guide.md) — covers all popular apps

**Q: Is PromptHub better than [alternative]?**
A: [Why PromptHub](07-why-prompthub-comparison.md) — detailed comparison

**Q: How do I save money on API costs?**
A: Use local models with PromptHub (see [Quick Start](01-quick-start-guide.md))

**Q: Can PromptHub remember information?**
A: Yes! [Session Memory Guide](03-session-memory-guide.md) explains how

**Q: Something isn't working**
A: [Troubleshooting Guide](05-troubleshooting-guide.md) — 95% of issues covered

**Q: I want to customize everything**
A: [Advanced Manual](08-advanced-power-user-manual.md) — for power users

**Q: Is my data private?**
A: Yes, completely local. See [Session Memory — Privacy](03-session-memory-guide.md#privacy-and-data)

---

## 📚 Related Documentation

These guides focus on end-user experience. For technical/developer documentation, see:
- `../architecture/` — System design and decisions
- `../api/` — API specification (OpenAPI 3.0) and integration examples
- `../features/` — Feature deep-dives (Memory System, LM Studio, etc.)
- `../modules/` — Module documentation

---

## 🎯 Learning Path Recommendations

### "I want to get PromptHub running TODAY"
→ [Quick Start Guide](01-quick-start-guide.md) (5 min)

### "I want to use it with my favorite app"
→ [Quick Start](01-quick-start-guide.md) → [App Configuration](06-client-configuration-guide.md)

### "I want to understand all the features"
→ [Quick Start](01-quick-start-guide.md) → [Enhancement](02-prompt-enhancement-user-guide.md) → [Memory](03-session-memory-guide.md) → [API](04-openai-api-guide.md)

### "I want to know if PromptHub is right for me"
→ [Why PromptHub](07-why-prompthub-comparison.md)

### "I want to troubleshoot a problem"
→ [Troubleshooting Guide](05-troubleshooting-guide.md) (Quick Diagnosis first)

### "I want to customize everything"
→ [Advanced Manual](08-advanced-power-user-manual.md)

---

## 💡 Pro Tips

- **Bookmark this index** — Easy reference for all guides
- **Skim the Troubleshooting guide once** — Useful to know what's covered
- **Use Command+F** — Search within guides for specific topics
- **Read in order** — Each guide builds on previous knowledge
- **Check logs first** — Often contains the exact error message

---

## 📞 Support

1. **Check the logs:** `tail ~/prompthub/logs/router-stderr.log`
2. **Run diagnostics:** `./scripts/diagnose.sh`
3. **Search this documentation** using Command+F
4. **Read the Troubleshooting Guide** — covers 95% of common issues
5. **Check the Advanced Manual** — for configuration help

---

**Last Updated:** March 2, 2026
**PromptHub Version:** Latest
**Documentation:** Non-Technical User Guides

Enjoy using PromptHub! 🚀
