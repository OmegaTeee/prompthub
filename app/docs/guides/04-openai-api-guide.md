# Using PromptHub as an OpenAI-Compatible API

## Overview

PromptHub can act as an **OpenAI-compatible API server** for your apps. This means apps that normally connect to OpenAI can instead connect to PromptHub and use local Ollama models or other backends.

### Why Use This?

- 💰 **Save money** — Use free local models instead of paying for API calls
- 🔒 **Privacy** — Your data stays on your computer
- ⚡ **Speed** — Local models respond faster (no internet latency)
- 🎯 **Flexibility** — Switch between Ollama models without changing app configuration

## Getting Started

### Step 1: Find Your API Key

Your API keys are in `~/.local/share/prompthub/configs/api-keys.json`. You should see something like:

```json
{
  "keys": {
    "sk-prompthub-code-001": {
      "client_name": "vscode",
      "enhance": false,
      "description": "VS Code (pass-through)"
    },
    "sk-prompthub-copilot-001": {
      "client_name": "vscode",
      "enhance": false,
      "description": "OAI Copilot"
    }
  }
}
```

Each key grants access to PromptHub's API. Keep these safe!

### Step 2: Configure Your App

For apps that support OpenAI API configuration:

| Setting | Value                                    |
| ------- | ---------------------------------------- |
| API URL | `http://localhost:9090/v1`               |
| API Key | `sk-prompthub-xxxx-xxx` (from step 1)    |
| Model   | Any model in Ollama (e.g., `gemma3:27b`) |

### Step 3: Test the Connection

Open Terminal and verify the API is working:

```bash
# List available models
curl -s http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-code-001"
```

You should see a list of models available in Ollama.

## Available Models

To see which models you have available:

```bash
# Via PromptHub API
curl http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-code-001"

# Or directly in Ollama
ollama list
```

To add a new model:
```bash
ollama pull gemma3:27b
```

It will now be available in PromptHub.

## Using the API

### Simple Chat Request

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-code-001" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:27b",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### With Enhancement

If you've enabled enhancement for your API key, PromptHub will automatically improve your prompts before sending to Ollama:

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-code-001" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:27b",
    "messages": [
      {"role": "system", "content": "You are helpful"},
      {"role": "user", "content": "Write a Python function"}
    ]
  }'
```

## App Configuration Examples

### VS Code

1. Install OpenAI extension (if not already installed)

2. Edit `settings.json`:

  ```json
    {
      "chat.models": [{
        "id": "gemma3:27b",
        "provider": "openaiCompatible",
        "url": "http://localhost:9090/v1",
        "apiKey": "sk-prompthub-code-001"
      }]
    }
    ```

3. Select the model in the chat panel

### Raycast

1. Open Raycast preferences
2. Search for "AI" settings
3. Choose "OpenAI Compatible"
4. Set:
   - **URL:** `http://localhost:9090/v1`
   - **API Key:** `sk-prompthub-code-001`
   - **Model:** `gemma3:27b`

### Custom Python Script

```python
import requests
import json

url = "http://localhost:9090/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-prompthub-code-001",
    "Content-Type": "application/json"
}
data = {
    "model": "gemma3:27b",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

## Managing API Keys

### Adding a New Key

Edit `~/.local/share/prompthub/configs/api-keys.json`:

```json
{
  "keys": {
    "sk-my-custom-key-001": {
      "client_name": "my-app",
      "enhance": true,
      "description": "My custom application"
    }
  }
}
```

Save and reload (no restart needed):
```bash
curl -X POST http://localhost:9090/v1/api-keys/reload
```

### Revoking a Key

1. Remove or comment out the key in `api-keys.json`
2. Reload: `curl -X POST http://localhost:9090/v1/api-keys/reload`
3. The key will no longer work

### Key Settings Explained

| Setting       | Options    | What it does                              |
| ------------- | ---------- | ----------------------------------------- |
| `client_name` | String     | Groups keys by app for enhancement rules  |
| `enhance`     | true/false | Whether to automatically enhance prompts  |
| `description` | String     | Human-readable label (for your reference) |

## Advanced: Enhancement Rules

If you enable enhancement for an API key, PromptHub uses the `client_name` to look up which enhancement model to use.

Edit `~/.local/share/prompthub/configs/enhancement-rules.json`:

```json
{
  "default": { "model": "gemma3:4b" },
  "clients": {
    "my-app": { "model": "gemma3:27b" }
  }
}
```

This means:
- By default, use the lightweight `gemma3:4b` for enhancement
- But for `my-app`, use the more powerful `gemma3:27b`

## Troubleshooting API Issues

### "401 Unauthorized"
**Problem:** API key is missing or invalid.

**Solution:**
1. Check that your key is in `api-keys.json`
2. Make sure the format is: `Authorization: Bearer sk-xxx`
3. Reload keys: `curl -X POST http://localhost:9090/v1/api-keys/reload`

### "404 Model not found"
**Problem:** The model doesn't exist in Ollama.

**Solution:**
```bash
# Pull the model first
ollama pull gemma3:27b

# Verify it's available
curl http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-code-001"
```

### "Connection refused"
**Problem:** PromptHub isn't running.

**Solution:**
```bash
# Start PromptHub
cd ~/.local/share/prompthub
uvicorn router.main:app --host 127.0.0.1 --port 9090
```

### "Enhancement timeout"
**Problem:** Enhancement is taking too long.

**Solution:**
1. Disable enhancement: Set `"enhance": false` in `api-keys.json`
2. Or use a faster model: `gemma3:4b` instead of `gemma3:27b`

### "Model loading error"
**Problem:** Ollama is busy or the model is corrupted.

**Solution:**
```bash
# Restart Ollama
killall ollama
ollama serve

# Re-pull the model if needed
ollama pull gemma3:27b
```

## Common Questions

**Q: Can I use both OpenAI AND Ollama models?**
A: PromptHub currently forwards to Ollama. If you need OpenAI, connect directly to OpenAI's API from your app.

**Q: Is there a rate limit?**
A: No hard limits, but very heavy usage might slow down your computer.

**Q: Can multiple apps use the same API key?**
A: Yes, but they'll share the same enhancement settings. Use different keys if you want different behavior.

**Q: What if I lose my API key?**
A: Just create a new one in `api-keys.json`. Lost keys can't be recovered, so don't share them!

## Performance Tips

- Use lightweight models (`gemma3:4b`) for fast responses
- Enable caching for repeated queries
- Monitor system resources (PromptHub + Ollama can use significant RAM)
- Close unused models to free up memory: `ollama rm model-name`

## Security

### Keep Your Keys Safe
- Never commit keys to version control
- Never share your API keys in public spaces
- If compromised, delete and recreate the key immediately

### Local-Only
- PromptHub is completely local — no data goes to external servers
- All API keys are stored on your computer only
- No authentication backend needed (unlike cloud APIs)

---

**Next:** See **Troubleshooting Guide** for common issues and solutions.
