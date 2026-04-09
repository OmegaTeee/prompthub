# Using PromptHub as an OpenAI-Compatible API

## What This Guide Covers

PromptHub can stand in for the OpenAI API. Any app that talks to OpenAI can talk to PromptHub instead, using your local LM Studio models.

Think of it like a translator: your app speaks "OpenAI," and PromptHub translates that into "LM Studio" behind the scenes.

### Why Use This?

- **Save money** -- Use free local models instead of paying for API calls.
- **Keep your data private** -- Everything stays on your computer.
- **Get faster responses** -- Local models skip the internet round-trip.
- **Stay flexible** -- Switch LM Studio models without touching app settings.

**Key takeaways:**
- PromptHub mimics the OpenAI API so your apps work without changes.
- Your data never leaves your machine.
- You can swap models anytime on the PromptHub side.

---

## Getting Started

### Step 1: Find Your API Key

Your API keys live in `~/prompthub/app/configs/api-keys.json`. Open that file and you will see something like this:

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

Each key grants access to the PromptHub API. Treat these like passwords -- keep them safe.

### Step 2: Configure Your App

Every app that supports the OpenAI API needs three settings. Fill them in like this:

| Setting | Value                                    |
| ------- | ---------------------------------------- |
| API URL | `http://localhost:9090/v1`               |
| API Key | `sk-prompthub-xxxx-xxx` (from step 1)   |
| Model   | Any model in LM Studio (e.g., `qwen3-4b-instruct-2507`) |

### Step 3: Test the Connection

Open Terminal and run this command to confirm things are working:

```bash
curl -s http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-code-001"
```

You should see a list of models available in LM Studio. If you get an error, see the Troubleshooting section at the end of this guide.

**Key takeaways:**
- You need an API key, the PromptHub URL, and a model name.
- Test with a `curl` command before configuring your app.

---

## Available Models

To see which models you have, use either of these commands:

```bash
# Via the PromptHub API
curl http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-code-001"

# Or directly through LM Studio
lms ls
```

To download a new model:

```bash
lms get qwen3-4b-instruct-2507
```

Once the download finishes, the model appears in PromptHub automatically. No restart needed.

---

## Using the API

### Send a Chat Request

This is the most common call. It sends a message and gets a response, like texting a chatbot:

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-code-001" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-4b-instruct-2507",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### Use Enhancement

Enhancement means PromptHub rewrites your prompt to get better results before sending it to LM Studio. Think of it like having an editor polish your question before asking the expert.

If enhancement is turned on for your API key, it happens automatically:

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-code-001" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-4b-instruct-2507",
    "messages": [
      {"role": "system", "content": "You are helpful"},
      {"role": "user", "content": "Write a Python function"}
    ]
  }'
```

**Key takeaways:**
- The chat endpoint follows the standard OpenAI format.
- Enhancement improves your prompts automatically when enabled.

---

## App Configuration Examples

### VS Code

1. Install an OpenAI extension if you do not already have one.
2. Edit `settings.json` and add this block:

    ```json
    {
      "chat.models": [{
        "id": "qwen3-4b-instruct-2507",
        "provider": "openaiCompatible",
        "url": "http://localhost:9090/v1",
        "apiKey": "sk-prompthub-code-001"
      }]
    }
    ```

3. Select the model in the chat panel.

### Raycast

1. Open Raycast preferences.
2. Search for "AI" settings.
3. Choose "OpenAI Compatible."
4. Fill in:
   - **URL:** `http://localhost:9090/v1`
   - **API Key:** `sk-prompthub-code-001`
   - **Model:** `qwen3-4b-instruct-2507`

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
    "model": "qwen3-4b-instruct-2507",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

---

## Managing API Keys

### Add a New Key

Open `~/prompthub/app/configs/api-keys.json` and add an entry:

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

Save the file, then reload without restarting:

```bash
curl -X POST http://localhost:9090/v1/api-keys/reload
```

### Revoke a Key

1. Remove or comment out the key in `api-keys.json`.
2. Reload the keys:
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```
3. That key will stop working immediately.

### Key Settings Explained

| Setting       | Options    | What It Does                              |
| ------------- | ---------- | ----------------------------------------- |
| `client_name` | String     | Groups keys by app for enhancement rules  |
| `enhance`     | true/false | Turns automatic prompt enhancement on or off |
| `description` | String     | A label for your own reference            |

**Key takeaways:**
- Add or remove keys by editing `api-keys.json` and reloading.
- No restart is required -- reload takes effect instantly.

---

## Advanced: Enhancement Rules

When enhancement is turned on for an API key, PromptHub uses the `client_name` to decide which model does the rewriting. You can customize this.

Edit `~/prompthub/app/configs/enhancement-rules.json`:

```json
{
  "default": { "model": "qwen3-4b-instruct-2507" },
  "clients": {
    "my-app": { "model": "qwen3-4b-instruct-2507" }
  }
}
```

All clients now use the same enhancement model (`qwen3-4b-instruct-2507`). You can still define per-client entries to customize the system prompt or timeout.

---

## Troubleshooting API Issues

### "401 Unauthorized"

**Problem:** The API key is missing or not recognized.

**Fix:**

1. Confirm your key is listed in `api-keys.json`.
2. Check the header format: `Authorization: Bearer sk-xxx`.
3. Reload the keys:
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```

### "404 Model not found"

**Problem:** The model you requested is not installed in LM Studio.

**Fix:**

```bash
# Download the model
lms get qwen3-4b-instruct-2507

# Confirm it appears in PromptHub
curl http://localhost:9090/v1/models \
  -H "Authorization: Bearer sk-prompthub-code-001"
```

### "Connection refused"

**Problem:** PromptHub is not running.

**Fix:**

```bash
cd ~/prompthub
uvicorn router.main:app --host 127.0.0.1 --port 9090
```

### "Enhancement timeout"

**Problem:** Prompt enhancement is taking too long. This usually means the enhancement model is too large for your hardware.

**Fix:**

1. Turn off enhancement: set `"enhance": false` in `api-keys.json`.
2. Check if LM Studio is busy with other tasks: run `lms ps`.

### "Model loading error"

**Problem:** LM Studio is busy loading another model or the model files are corrupted.

**Fix:**

```bash
# Stop the LM Studio server (if running)
lms server stop || true
# Start the LM Studio server
lms server start

# Re-download the model if needed
lms get qwen3-4b-instruct-2507
```

---

## Common Questions

**Q: Can I use both OpenAI AND LM Studio models?**

A: PromptHub forwards requests to LM Studio. If you need OpenAI models, connect your app directly to OpenAI's API.

**Q: Is there a rate limit?**

A: There is no hard limit. Heavy usage may slow your computer since LM Studio runs locally.

**Q: Can multiple apps use the same API key?**

A: Yes. They will share the same enhancement settings. Create separate keys if you want different behavior per app.

**Q: What if I lose my API key?**

A: Create a new one in `api-keys.json`. Lost keys cannot be recovered, so store them somewhere safe.

---

## Performance Tips

- **Use lightweight models** like `qwen3-4b-instruct-2507` for faster responses.
- **Enable caching** so repeated queries return instantly.
- **Watch your RAM** -- PromptHub and LM Studio together can use a lot of memory.
- **Unload unused models** to free resources:
  ```bash
  lms rm model-name
  ```

---

## Security

### Keep Your Keys Safe

- Never commit keys to version control.
- Never share keys in public spaces.
- If a key is compromised, delete it from `api-keys.json` and create a new one right away.

### Everything Stays Local

PromptHub is fully local. No data leaves your computer. All API keys are stored on your machine only. There is no external authentication service to worry about.

**Key takeaways:**
- Treat API keys like passwords.
- All traffic stays on localhost -- nothing goes to the internet.

---

**Next:** See the **Troubleshooting Guide** for more common issues and solutions.
