# App Configuration Guide

## Overview

This guide shows you how to connect your favorite apps to PromptHub. Each app has slightly different configuration steps, but the basic idea is the same:

1. Tell the app where PromptHub is (`http://localhost:9090`)
2. Give it your API key (`sk-your-key`)
3. Tell it which model to use
4. Start using AI features!

## Supported Apps

PromptHub works with any app that supports:
- **MCP** (Model Context Protocol) — direct integration
- **OpenAI API** — compatible interface
- **Custom HTTP API** — for any app with custom integration

## Claude Desktop (Official App)

### Configuration

1. **Open** `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **Add PromptHub as an MCP server:**

    ```json
    {
      "mcpServers": {
        "prompthub": {
          "command": "uvicorn",
          "args": [
            "router.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "9090"
          ],
          "cwd": "~/.local/share/prompthub/app"
        }
      }
    }
    ```

3. **Restart Claude** — Close and reopen the app

4. **Verify connection:**
   - Open Claude and look for the "Tools" icon
   - You should see PromptHub listed
   - Click it to confirm it's connected

### First Test

Once connected, try asking Claude:

> "What tools do you have available from PromptHub?"

Claude should list the available MCP servers and tools.

---

## VS Code

### Option A: OpenAI API (Recommended)

1. **Install extension:**
   - Open VS Code Extensions (`Cmd+Shift+X`)
   - Search for "OpenAI" or "Chat Copilot"
   - Install your preferred extension

2. **Configure VS Code settings:**
   - Open `Code > Settings > Settings` (`Cmd+,`)
   - Search for `chat.openaiCompatible`
   - Enable it

3. **Add PromptHub configuration:**
   ```json
   {
     "chat.openaiCompatibleEndpoint": "http://localhost:9090/v1",
     "chat.openaiCompatibleApiKey": "sk-prompthub-code-001",
     "chat.openaiCompatibleModel": "gemma3:27b"
   }
   ```

4. **Test:**
   - Open a chat panel in VS Code
   - You should see PromptHub as an option
   - Send a message to test

### Option B: Direct MCP Connection

For advanced users, configure VS Code to connect directly to PromptHub's MCP servers:

1. Edit your VS Code settings.json:
   ```json
   {
     "mcp": {
       "servers": {
         "prompthub": {
           "command": "uvicorn",
           "args": ["router.main:app", "--port", "9090"]
         }
       }
     }
   }
   ```

2. Restart VS Code

---

## Open WebUI

Open WebUI connects to PromptHub via two channels:
- **Chat**: OpenAI-compatible `/v1/` proxy for conversations
- **Tools**: Streamable HTTP gateway (`/mcp-direct/mcp`) for MCP tool access

### Configuration

1. **Add PromptHub as an OpenAI connection** in Open WebUI Admin > Connections:
   - URL: `http://127.0.0.1:9090/v1`
   - API Key: `sk-prompthub-openwebui-001`

2. **Add MCP tools** in Admin > Settings > Tools > MCP Servers:
   - URL: `http://127.0.0.1:9090/mcp-direct/mcp`
   - No auth required (local-only endpoint)

3. **Select a model** in the chat dropdown (e.g., `gemma3:4b` for fast responses)

### Filtering Tools with GATEWAY_SERVERS

By default, the gateway exposes all configured MCP servers (~58 tools). For smaller models, reduce the tool count by setting `GATEWAY_SERVERS` in `app/.env`:

```bash
# Only expose these servers to the gateway
GATEWAY_SERVERS="context7,desktop-commander,sequential-thinking"
```

Empty value (default) = all servers. Restart the router after changing.

### Performance Tips

- **Disable enhancement**: Set `"enhance": false` in `api-keys.json` for the Open WebUI key to skip the prompt rewrite step
- **Use smaller models**: `gemma3:4b` is fastest; `gemma3:27b` is more capable but slower
- **Reduce tool count**: Use `GATEWAY_SERVERS` to limit exposed tools — fewer tools means faster tool selection by the model

---

## Raycast

### Using OpenAI-Compatible API

1. **Open Raycast Settings** (`Cmd+,`)

2. **Search for "AI"** and select **"AI Settings"**

3. **Choose OpenAI Compatible:**
   - Model Provider: **OpenAI Compatible**
   - API Endpoint: `http://localhost:9090/v1`
   - API Key: `sk-prompthub-copilot-001` (or your key)
   - Model: `gemma3:27b` (or your preferred model)

4. **Test:**
   - Open Raycast (`Cmd+Space`)
   - Type "Ask AI" and send a question
   - Should work with local Ollama models

---

## Python Scripts & Automation

### Using requests library

```python
import requests
import json

def call_prompthub(prompt, model="gemma3:27b"):
    url = "http://localhost:9090/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-prompthub-code-001",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Usage
result = call_prompthub("Write a Python function to calculate fibonacci")
print(result['choices'][0]['message']['content'])
```

### Using curl in bash scripts

```bash
#!/bin/bash

PROMPT="$1"
MODEL="${2:-gemma3:27b}"
API_KEY="sk-prompthub-code-001"

curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"$PROMPT\"}
    ]
  }" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

Usage:
```bash
chmod +x prompthub.sh
./prompthub.sh "Explain quantum computing"
```

---

## Obsidian (Notes App)

### Integration via Custom Plugin

1. **Enable Community Plugins:**
   - Settings > Community Plugins > Turn on

2. **Install "OpenAI Copilot" plugin:**
   - Browse > Search "OpenAI"
   - Install from your preferred OpenAI plugin

3. **Configure for PromptHub:**
   - Plugin settings > API endpoint: `http://localhost:9090/v1`
   - API key: `sk-prompthub-code-001`
   - Model: `gemma3:27b`

4. **Use in notes:**
   - Type `/ai` and ask questions
   - Results appear inline

---

## Automator & Shell Scripts

### Create an Automator Service

1. **Open Automator** (`Applications > Automator`)

2. **Create New > Quick Action**

3. **Add "Run Shell Script" action:**
   ```bash
   API_KEY="sk-prompthub-code-001"
   PROMPT="$1"

   curl -s http://localhost:9090/v1/chat/completions \
     -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d "{
       \"model\": \"gemma3:27b\",
       \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}]
     }" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['choices'][0]['message']['content'])"
   ```

4. **Save as "Ask PromptHub"**

5. **Use with Keyboard Shortcut:**
   - System Settings > Keyboard > Shortcuts > Services
   - Assign a shortcut to "Ask PromptHub"

---

## Keyboard Maestro

### Simple Prompt Enhancement Macro

```
1. Trigger: Custom keyboard shortcut
2. Action: Prompt with hidden answer "%Prompt%"
3. Action: Execute shell script:
   API_KEY="sk-prompthub-code-001"
   PROMPT="%Variable%Prompt%"

   curl -s http://localhost:9090/v1/chat/completions \
     -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d "{
       \"model\": \"gemma3:27b\",
       \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}]
     }" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

4. Action: Paste result into front app
```

---

## Node.js / JavaScript

### Using npm package

```bash
npm install axios
```

```javascript
const axios = require('axios');

async function callPromptHub(prompt) {
  try {
    const response = await axios.post(
      'http://localhost:9090/v1/chat/completions',
      {
        model: 'gemma3:27b',
        messages: [{ role: 'user', content: prompt }]
      },
      {
        headers: {
          'Authorization': 'Bearer sk-prompthub-code-001',
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data.choices[0].message.content;
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Usage
callPromptHub('Write JavaScript code').then(console.log);
```

---

## Generic HTTP Client Setup

### Postman / Insomnia

1. **Create new request:**
   - Method: `POST`
   - URL: `http://localhost:9090/v1/chat/completions`

2. **Headers tab:**
   ```
   Authorization: Bearer sk-prompthub-code-001
   Content-Type: application/json
   ```

3. **Body tab (JSON):**
   ```json
   {
     "model": "gemma3:27b",
     "messages": [
       {
         "role": "user",
         "content": "Your prompt here"
       }
     ]
   }
   ```

4. **Send** and see the response!

---

## Troubleshooting App Configuration

### "Cannot connect to localhost:9090"

1. Is PromptHub running?
   ```bash
   lsof -i :9090
   ```

2. Try the test URL in browser:
   ```
   http://localhost:9090/health
   ```

### "Invalid API key"

1. Check key format: `Authorization: Bearer sk-xxx`
2. Verify key exists in `api-keys.json`
3. Reload keys: `curl -X POST http://localhost:9090/v1/api-keys/reload`

### "Model not found"

1. List available models:
   ```bash
   ollama list
   ```
2. Pull missing model:
   ```bash
   ollama pull gemma3:27b
   ```

### "Enhancement is slow"

1. Disable enhancement for that app
2. Or use a faster model: `gemma3:4b`

---

## API Key Best Practices

### Use Different Keys for Different Apps

Instead of using the same key everywhere, create app-specific keys:

```json
{
  "keys": {
    "sk-claude-001": { "client_name": "claude", "enhance": true },
    "sk-vscode-001": { "client_name": "vscode", "enhance": false },
    "sk-raycast-001": { "client_name": "raycast", "enhance": false }
  }
}
```

Benefits:
- Can disable one app without affecting others
- Different enhancement settings per app
- Easier to track which app is using which key
- Can revoke access to specific apps

### Keep Keys Secure

- ❌ Don't put keys in version control
- ❌ Don't share keys in chat/email
- ❌ Don't post keys in public forums
- ✅ Store in `.env` files (if needed)
- ✅ Use environment variables where possible
- ✅ If compromised, delete and create new key immediately

---

## Performance Tips

### For Faster Responses

1. Use lighter models:
   ```
   gemma3:4b (fastest)
   gemma3:7b (fast)
   gemma3:27b (more capable)
   ```

2. Disable enhancement if not needed:
   ```json
   "enhance": false
   ```

3. Keep fewer models loaded:
   ```bash
   # See what's loaded
   ollama list

   # Remove unused models
   ollama rm model-name
   ```

### For Better Results

1. Use larger models (but slower):
   ```
   gemma3:27b (more thoughtful)
   ```

2. Enable enhancement (adds context):
   ```json
   "enhance": true
   ```

3. Provide context in your prompts:
   > "I'm a Python developer. Write a function that..."

---

## Summary Table

| App | Setup Difficulty | Enhancement | Memory | Notes |
|-----|------------------|-------------|--------|-------|
| Claude Desktop | Easy | Yes (MCP) | Yes | Direct integration |
| VS Code | Easy | Yes | No | Via OpenAI API |
| Open WebUI | Easy | Optional | No | Chat + MCP tools via gateway |
| Raycast | Medium | Yes | No | Via OpenAI API |
| Python Scripts | Easy | Yes | Yes | Use requests library |
| Bash Scripts | Easy | No | No | Use curl |
| Automator | Medium | No | No | Shell script wrapper |
| Custom Apps | Varies | Yes | Yes | Use HTTP API |

---

**Next:** See **Troubleshooting Guide** if configuration doesn't work.
