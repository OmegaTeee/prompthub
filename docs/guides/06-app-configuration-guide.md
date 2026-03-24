# App Configuration Guide

## What This Guide Covers

This guide shows you how to connect your favorite apps to PromptHub. Every app follows the same basic pattern:

1. Tell the app where PromptHub is: `http://localhost:9090`
2. Give it your API key: `sk-your-key`
3. Pick a model to use.
4. Start chatting.

Think of PromptHub as a switchboard. Your apps call in, and PromptHub routes the request to the right AI model running on your machine.

## Supported Connection Types

PromptHub works with any app that supports one of these:

- **MCP (Model Context Protocol)** -- Direct tool integration. The app can call MCP tools through PromptHub.
- **OpenAI API** -- A compatible interface. The app thinks it is talking to OpenAI, but PromptHub handles the request locally.
- **Custom HTTP API** -- For apps with their own integration layer.

**Key takeaways:**
- Three connection types cover almost every app.
- MCP gives tool access; OpenAI API gives chat access.

---

## Claude Desktop (Official App)

### Configuration

1. Open this file in a text editor:
   ```
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. Add PromptHub as an MCP server:

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
          "cwd": "~/prompthub/app"
        }
      }
    }
    ```

3. Restart Claude by closing and reopening the app.

4. Verify the connection:
   - Open Claude and look for the "Tools" icon.
   - You should see PromptHub listed.
   - Click it to confirm it is connected.

### First Test

Once connected, try asking Claude:

> "What tools do you have available from PromptHub?"

Claude should list the available MCP servers and tools.

**Key takeaways:**
- Claude Desktop uses MCP for a direct connection.
- After editing the config, you must restart Claude.

---

## VS Code

### Option A: OpenAI API (Recommended)

This is the easier setup. It gives you chat access through PromptHub.

1. Open VS Code Extensions (`Cmd+Shift+X`).
2. Search for "OpenAI" or "Chat Copilot" and install your preferred extension.
3. Open Settings (`Cmd+,`) and search for `chat.openaiCompatible`. Enable it.
4. Add this to your `settings.json`:

   ```json
   {
     "chat.openaiCompatibleEndpoint": "http://localhost:9090/v1",
     "chat.openaiCompatibleApiKey": "sk-prompthub-code-001",
     "chat.openaiCompatibleModel": "gemma3:27b"
   }
   ```

5. Open a chat panel in VS Code. You should see PromptHub as an option. Send a test message.

### Option B: Direct MCP Connection

For users who want MCP tool access inside VS Code:

1. Edit your VS Code `settings.json`:

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

2. Restart VS Code.

**Key takeaways:**
- Option A (OpenAI API) is the quickest way to get chat working.
- Option B (MCP) gives you tool access but requires more setup.

---

## Open WebUI

Open WebUI connects to PromptHub through two channels:

- **Chat:** Uses the OpenAI-compatible `/v1/` proxy for conversations.
- **Tools:** Uses the Streamable HTTP gateway (`/mcp-direct/mcp`) for MCP tool access.

Think of it like a phone with two lines -- one for talking, one for actions.

### Configuration

1. Add PromptHub as an OpenAI connection in **Admin > Connections**:
   - URL: `http://127.0.0.1:9090/v1`
   - API Key: `sk-prompthub-openwebui-001`

2. Add MCP tools in **Admin > Settings > Tools > MCP Servers**:
   - URL: `http://127.0.0.1:9090/mcp-direct/mcp`
   - No auth required (this is a local-only endpoint).

3. Select a model in the chat dropdown (e.g., `gemma3:4b` for fast responses).

### Filtering Tools with GATEWAY_SERVERS

By default, the gateway exposes all configured MCP servers (around 58 tools). Smaller models work better with fewer tools. To limit which servers appear, set `GATEWAY_SERVERS` in `app/.env`:

```bash
# Only expose these servers to the gateway
GATEWAY_SERVERS="context7,desktop-commander,sequential-thinking"
```

Leave it empty (the default) to expose all servers. Restart the router after changing this value.

### Performance Tips

- **Turn off enhancement:** Set `"enhance": false` in `api-keys.json` for the Open WebUI key. This skips the prompt rewrite step.
- **Use smaller models:** `gemma3:4b` is fastest. `gemma3:27b` is more capable but slower.
- **Reduce tool count:** Use `GATEWAY_SERVERS` to limit exposed tools. Fewer tools means the model picks the right one faster.

**Key takeaways:**
- Open WebUI needs two connections: one for chat, one for tools.
- Use `GATEWAY_SERVERS` to keep the tool list manageable for smaller models.

---

## Raycast

### Using OpenAI-Compatible API

1. Open Raycast Settings (`Cmd+,`).
2. Search for "AI" and select "AI Settings."
3. Choose "OpenAI Compatible" and fill in:
   - **Model Provider:** OpenAI Compatible
   - **API Endpoint:** `http://localhost:9090/v1`
   - **API Key:** `sk-prompthub-raycast-001` (or your key)
   - **Model:** `gemma3:27b` (or your preferred model)
4. Test it: open Raycast (`Cmd+Space`), type "Ask AI," and send a question.

**Key takeaways:**
- Raycast connects through the OpenAI-compatible API.
- Setup takes about one minute.

---

## Python Scripts and Automation

### Using the requests Library

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

### Using curl in Bash Scripts

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

Save this as `prompthub.sh`, make it executable, and run it:

```bash
chmod +x prompthub.sh
./prompthub.sh "Explain quantum computing"
```

**Key takeaways:**
- Python and Bash scripts follow the standard OpenAI request format.
- Both examples are copy-paste ready.

---

## Obsidian (Notes App)

### Integration via Plugin

1. Go to **Settings > Community Plugins** and turn on community plugins.
2. Click **Browse**, search for "OpenAI," and install your preferred plugin.
3. In the plugin settings, configure:
   - API endpoint: `http://localhost:9090/v1`
   - API key: `sk-prompthub-code-001`
   - Model: `gemma3:27b`
4. In your notes, type `/ai` and ask a question. Results appear inline.

---

## Automator and Shell Scripts

You can create a macOS Quick Action that sends selected text to PromptHub. This lets you highlight text anywhere and get an AI response.

### Create an Automator Service

1. Open **Automator** (in Applications).
2. Choose **New > Quick Action**.
3. Add a "Run Shell Script" action with this script:

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

4. Save it as "Ask PromptHub."
5. Assign a keyboard shortcut: go to **System Settings > Keyboard > Shortcuts > Services** and pick a shortcut for "Ask PromptHub."

---

## Keyboard Maestro

### Prompt Enhancement Macro

Here is a macro that pops up a prompt box, sends your text to PromptHub, and pastes the response:

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

### Using axios

First, install the package:

```bash
npm install axios
```

Then use this code:

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

## Generic HTTP Client Setup (Postman / Insomnia)

These steps work for any HTTP client:

1. Create a new request:
   - Method: `POST`
   - URL: `http://localhost:9090/v1/chat/completions`

2. Set the headers:
   ```
   Authorization: Bearer sk-prompthub-code-001
   Content-Type: application/json
   ```

3. Set the body (JSON):
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

4. Click **Send** and check the response.

---

## Troubleshooting App Configuration

### "Cannot connect to localhost:9090"

1. Check if PromptHub is running:
   ```bash
   lsof -i :9090
   ```

2. Open this URL in your browser to verify:
   ```
   http://localhost:9090/health
   ```

### "Invalid API key"

1. Confirm the header format: `Authorization: Bearer sk-xxx`
2. Verify the key exists in `api-keys.json`.
3. Reload the keys:
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```

### "Model not found"

1. List available models:
   ```bash
   ollama list
   ```
2. Download the missing model:
   ```bash
   ollama pull gemma3:27b
   ```

### "Enhancement is slow"

1. Turn off enhancement for that app's key in `api-keys.json`.
2. Or switch to a faster model: `gemma3:4b`.

**Key takeaways:**
- Most connection issues come down to PromptHub not running or a wrong API key.
- The health endpoint (`/health`) is the fastest way to check if PromptHub is alive.

---

## API Key Best Practices

### Use a Different Key for Each App

Instead of sharing one key everywhere, create a separate key per app:

```json
{
  "keys": {
    "sk-claude-001": { "client_name": "claude", "enhance": true },
    "sk-vscode-001": { "client_name": "vscode", "enhance": false },
    "sk-raycast-001": { "client_name": "raycast", "enhance": false }
  }
}
```

This gives you several benefits:

- You can disable one app without affecting others.
- Each app can have different enhancement settings.
- You can track which app is making which requests.
- You can revoke access for a single app.

### Keep Keys Secure

**Do not** put keys in version control, share them in chat or email, or post them in public forums.

**Do** store them in `.env` files when needed, use environment variables where possible, and delete compromised keys immediately.

**Key takeaways:**
- One key per app gives you fine-grained control.
- Treat keys like passwords -- never share them publicly.

---

## Performance Tips

### For Faster Responses

1. Use lighter models:
   ```
   gemma3:4b   (fastest)
   gemma3:7b   (fast)
   gemma3:27b  (more capable, slower)
   ```

2. Turn off enhancement if you do not need it:
   ```json
   "enhance": false
   ```

3. Keep fewer models loaded in memory:
   ```bash
   # See what is loaded
   ollama list

   # Remove unused models
   ollama rm model-name
   ```

### For Better Results

1. Use larger models (they are slower but more thoughtful):
   ```
   gemma3:27b
   ```

2. Turn on enhancement (adds context to your prompts):
   ```json
   "enhance": true
   ```

3. Give the model context in your prompts. For example:
   > "I am a Python developer. Write a function that..."

**Key takeaways:**
- Smaller models are faster; larger models give better answers.
- Enhancement adds a rewrite step that can improve quality at the cost of speed.

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

**Next:** See the [Troubleshooting Guide](05-troubleshooting-guide.md) if your configuration is not working.
