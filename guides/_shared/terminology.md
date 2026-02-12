# PromptHub Terminology Guide

**Purpose:** Standardized terminology used throughout all PromptHub documentation.

> **Why this matters:** Consistent terminology reduces confusion and makes documentation easier to search and understand.

---

## Core Terms

### PromptHub
**The correct name for this project.**

✅ **Use:** "PromptHub"
❌ **Don't use:** "router", "AI Agent Hub", "the hub", "agent-hub"

**Example:**
- ✅ "PromptHub provides a centralized MCP router"
- ❌ "The router provides centralized MCP access"

---

### MCP Server
**A service that provides tools/resources via the Model Context Protocol.**

✅ **Use:** "MCP server"
❌ **Don't use:** "server", "tool", "integration", "MCP tool", "service"

**Example:**
- ✅ "The filesystem MCP server provides file operations"
- ❌ "The filesystem tool provides file operations"

**Context:** MCP servers are the backend services (fetch, filesystem, brave-search, etc.) that PromptHub manages and routes requests to.

---

### Client
**An application that connects to PromptHub (Claude Desktop, VS Code, Raycast, etc.).**

✅ **Use:** "client"
❌ **Don't use:** "app", "application", "frontend", "user agent"

**Example:**
- ✅ "Each client can have custom enhancement rules"
- ❌ "Each application can have custom enhancement rules"

**Context:** Clients are identified by the `X-Client-Name` header they send to PromptHub.

---

### Enhancement
**The process of improving prompts with Ollama before sending to MCP servers.**

✅ **Use:** "enhancement", "prompt enhancement"
❌ **Don't use:** "auto-enhancement", "prompt improvement", "AI enhancement", "enrichment"

**Example:**
- ✅ "Enhancement is triggered by the `X-Enhance: true` header"
- ❌ "Auto-enhancement improves prompts automatically"

**Context:** Enhancement uses Ollama models (DeepSeek-R1, Qwen3-Coder) to add context and improve prompt quality.

---

### Circuit Breaker
**A resilience pattern that prevents cascading failures.**

✅ **Use:** "circuit breaker" (two words)
❌ **Don't use:** "circuit-breaker", "CB", "breaker", "fault protector"

**Example:**
- ✅ "The circuit breaker opens after 3 consecutive failures"
- ❌ "The CB trips after 3 failures"

**Context:** Circuit breaker states: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery).

---

## Configuration Terms

### LaunchAgent
**macOS system service that auto-starts PromptHub on login.**

✅ **Use:** "LaunchAgent" (capitalized, no space)
❌ **Don't use:** "launch agent", "launchagent", "startup service", "daemon"

**Example:**
- ✅ "Install the LaunchAgent to start PromptHub automatically"
- ❌ "Install the launch agent for auto-start"

---

### Keychain
**macOS Keychain Access system for secure credential storage.**

✅ **Use:** "Keychain" or "macOS Keychain" (capitalized)
❌ **Don't use:** "keychain", "key chain", "credential store", "secrets manager"

**Example:**
- ✅ "Store API keys in macOS Keychain"
- ❌ "Store API keys in the credential store"

---

## Technical Terms

### Health Check
**Endpoint or command to verify PromptHub is running.**

✅ **Use:** "health check" (two words)
❌ **Don't use:** "healthcheck", "health-check", "status check", "ping"

**Example:**
- ✅ "Run a health check: `curl http://localhost:9090/health`"
- ❌ "Run a healthcheck to verify status"

---

### Dashboard
**Web UI for monitoring PromptHub at <http://localhost:9090/dashboard>**

✅ **Use:** "dashboard", "monitoring dashboard"
❌ **Don't use:** "web UI", "control panel", "admin panel", "console"

**Example:**
- ✅ "View real-time metrics in the dashboard"
- ❌ "View metrics in the admin panel"

---

### Audit Log
**Persistent record of all PromptHub operations for security and compliance.**

✅ **Use:** "audit log" (two words, singular)
❌ **Don't use:** "audit-log", "audit logs" (when referring to the system), "activity log", "event log"

**Example:**
- ✅ "The audit log records all credential access"
- ❌ "Audit logs track all operations"

**Note:** Use "audit logs" (plural) only when referring to multiple log entries, not the system itself.

---

## API Terms

### Endpoint
**A URL path that accepts HTTP requests (e.g., /health, /mcp/{server}/{path}).**

✅ **Use:** "endpoint"
❌ **Don't use:** "API", "route", "path", "URL"

**Example:**
- ✅ "The health endpoint returns server status"
- ❌ "The health API returns server status"

---

### JSON-RPC
**Protocol used by MCP servers for request/response communication.**

✅ **Use:** "JSON-RPC" (hyphenated, uppercase)
❌ **Don't use:** "JSONRPC", "json-rpc", "RPC", "JSON RPC"

**Example:**
- ✅ "PromptHub proxies JSON-RPC requests to MCP servers"
- ❌ "PromptHub proxies RPC requests to servers"

---

## File & Directory Terms

### Configuration File
**JSON files that configure PromptHub behavior.**

✅ **Use:** "config file", "configuration file"
❌ **Don't use:** "settings file", "config", "setup file"

**Example:**
- ✅ "Edit the config file at `configs/mcp-servers.json`"
- ❌ "Edit the settings at `configs/mcp-servers.json`"

---

### Working Directory
**The directory where PromptHub is installed (default: `~/.local/share/prompthub`).**

✅ **Use:** "working directory", "PromptHub directory"
❌ **Don't use:** "install directory", "project folder", "root directory"

**Example:**
- ✅ "Navigate to the working directory: `cd ~/.local/share/prompthub`"
- ❌ "Navigate to the install folder"

---

## Status & State Terms

### Running / Stopped
**Server operational states.**

✅ **Use:** "running", "stopped"
❌ **Don't use:** "active/inactive", "up/down", "online/offline", "started/halted"

**Example:**
- ✅ "Check if PromptHub is running"
- ❌ "Check if PromptHub is online"

---

### Enabled / Disabled
**Feature or setting states.**

✅ **Use:** "enabled", "disabled"
❌ **Don't use:** "on/off", "activated/deactivated", "turned on/off"

**Example:**
- ✅ "Enhancement is enabled by default"
- ❌ "Enhancement is turned on by default"

---

## Common Abbreviations

| Abbreviation | Full Term | Usage |
|--------------|-----------|-------|
| MCP | Model Context Protocol | ✅ Use freely after first mention |
| API | Application Programming Interface | ✅ Use freely |
| CLI | Command-Line Interface | ✅ Use freely after first mention |
| JSON | JavaScript Object Notation | ✅ Use freely |
| HTTP | Hypertext Transfer Protocol | ✅ Use in technical contexts |
| HTTPS | HTTP Secure | ✅ Use in technical contexts |
| URL | Uniform Resource Locator | ✅ Use freely |

❌ **Don't use without explanation:**
- CB (circuit breaker)
- AI (artificial intelligence - say "LLM" or "model")
- ENV (environment variables - spell out)

---

## Version References

### Software Versions
**How to refer to version numbers.**

✅ **Use:** "Python 3.11+", "Node.js 20.x", "PromptHub v0.1.0"
❌ **Don't use:** "Python 3.11 or higher", "Node version 20", "PromptHub 0.1.0"

**Example:**
- ✅ "Requires Python 3.11+"
- ❌ "Requires Python 3.11 or above"

---

## Quick Reference

### Most Common Mistakes

| ❌ Don't Say | ✅ Say Instead |
|--------------|----------------|
| "the router" | "PromptHub" |
| "MCP tool" | "MCP server" |
| "app" | "client" |
| "auto-enhancement" | "enhancement" |
| "circuit-breaker" | "circuit breaker" |
| "launch agent" | "LaunchAgent" |
| "healthcheck" | "health check" |
| "admin panel" | "dashboard" |

---

## When in Doubt

If you're unsure about terminology:

1. **Check this guide first** - Use Command+F to search
2. **Look at existing docs** - See how terms are used in other guides
3. **Prefer clarity over brevity** - "MCP server" is better than "server"
4. **Ask for guidance** - Open an issue if terminology is unclear

---

**Last Updated:** 2026-02-05
**Maintainer:** PromptHub Documentation Team

