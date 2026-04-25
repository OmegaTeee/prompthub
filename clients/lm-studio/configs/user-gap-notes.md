# Current scope

## 1. Using LM Studio as a local LLM provider
Guidance on using LM Studio as a local LLM provider for Qwen 2.5 & 3 Models for chat, tools and thinking for Apple M3 Max (macOS 26.3) — 36GB RAM, 28.08GB Metal VRAM. Optimize use of PromptHub mcp-bridge, proxy and router. Id like manage settings, instructions and prompt templates via PromptHub vs ephemral config in LM Studios.

---
## 2. Setting up local-first AI clients and tools
How to setup clients like [Cherry Studio](https://github.com/cherryhq/cherry-studio) or [Open WebUI](https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/). Enabling agentic coding with [huytd/supercoder](https://github.com/huytd/supercoder) or [qwen-coder](https://qwen.readthedocs.io/en/latest/run_locally/lmstudio.html)

  - Can I use code agents in Cherry Studio
  - Can AI drawing in Cherry Studio use local models
  - How to setup project and personal knowledge base
  - Can I customize the quick assistant and selection assistant in my mac taskbar

---

## 3. Local Project's Prompt engineering for local LLMs
Documentation and best practices for prompt engineering and templates for local LLMs, including how to use PromptHub to manage and enhance prompts for local LLMs. This includes best practices for structuring prompts, using tools and reasoning content, and optimizing prompts for local LLMs.

  - Default path: `/Users/visualval/.local/share/prompthub`
  - The project itself. A local MCP router with prompt enhancement middleware, running on localhost:9090. Not a gateway (doesn't consolidate tools), not just a bridge (does more than transport translation). Best described as an MCP service mesh for a single machine.
