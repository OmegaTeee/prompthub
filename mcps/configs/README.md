# Desktop MCP Configurations

Folder contains desktop client configuration files for connecting to PromptHub MCPs.

## MCP Inspector Integration

The mcp-inspector.json you saved is now tracked in the configs directory. This gives you a clean setup for testing the MCP bridge in isolation:

**To use it:**

```bash
cd mcps
node prompthub-bridge.js
```
Access the inspector here: [http://localhost:6274](http://localhost:6274)

**What you'll find:**

The Inspector is connected to your prompthub-bridge.js and showing all 7 aggregated MCP servers from PromptHub:
- ✅ context7 — Documentation & code search
- ✅ desktop-commander — File operations, shell commands
- ✅ sequential-thinking — Deep reasoning with chain-of-thought
- ✅ memory — Session management system (just implemented!)
- ✅ deepseek-reasoner — Extended reasoning capability
- ✅ duckduckgo — Web search
- ✅ perplexity — AI search

What you can do in the Inspector:

1. Browse Tools — See all 50+ aggregated tools with descriptions and schemas
2. Test Tools — Call any tool directly with test parameters
3. Inspect Requests — See raw JSON-RPC requests/responses
4. Check Server Status — Verify the bridge is healthy and discovering servers

Pro Tips:

- The bridge auto-discovers running servers from PromptHub every time you list tools
- Tool names are prefixed (e.g., context7_web_search) to avoid conflicts
- You can test memory system endpoints here: memory_add_fact, memory_get_session, etc.
- The Inspector communicates via stdio — same protocol Claude Desktop uses

Open [http://localhost:6274](http://localhost:6274) in your browser to explore! 🚀
