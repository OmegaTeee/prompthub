# API Integration Examples

Developer examples for calling PromptHub's OpenAI-compatible API from scripts and tools.

For desktop app setup (Claude, VS Code, Raycast), see the [App Configuration Guide](../guides/06-client-configuration-guide.md).

---

## curl

The simplest way to test the API:

```bash
curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-default-001" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3-4b-2507",
    "messages": [{"role": "user", "content": "Hello"}]
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### Shell script wrapper

```bash
#!/bin/bash
PROMPT="$1"
MODEL="${2:-qwen/qwen3-4b-2507}"
API_KEY="sk-prompthub-default-001"

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

Save as `prompthub.sh`, make executable, and run:

```bash
chmod +x prompthub.sh
./prompthub.sh "Explain quantum computing"
```

---

## Python

### Using requests

```python
import requests

def call_prompthub(prompt, model="qwen/qwen3-4b-2507"):
    response = requests.post(
        "http://localhost:9090/v1/chat/completions",
        headers={
            "Authorization": "Bearer sk-prompthub-default-001",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    return response.json()["choices"][0]["message"]["content"]

print(call_prompthub("Write a Python fibonacci function"))
```

### Using the OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:9090/v1",
    api_key="sk-prompthub-default-001",
)

response = client.chat.completions.create(
    model="qwen/qwen3-4b-2507",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

---

## JavaScript / Node.js

### Using fetch (built-in, no dependencies)

```javascript
async function callPromptHub(prompt) {
  const response = await fetch('http://localhost:9090/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer sk-prompthub-default-001',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'qwen/qwen3-4b-2507',
      messages: [{ role: 'user', content: prompt }],
    }),
  });

  const data = await response.json();
  return data.choices[0].message.content;
}

callPromptHub('Write a haiku about code').then(console.log);
```

### Using the OpenAI SDK

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:9090/v1',
  apiKey: 'sk-prompthub-default-001',
});

const response = await client.chat.completions.create({
  model: 'qwen/qwen3-4b-2507',
  messages: [{ role: 'user', content: 'Hello' }],
});
console.log(response.choices[0].message.content);
```

---

## macOS Automator (Quick Action)

Create a system-wide keyboard shortcut that sends selected text to PromptHub:

1. Open **Automator** > New > **Quick Action**.
2. Set "Workflow receives" to **text** in **any application**.
3. Add a **Run Shell Script** action:

```bash
API_KEY="sk-prompthub-default-001"
PROMPT="$1"

curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen/qwen3-4b-2507\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}]
  }" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

1. Save as "Ask PromptHub."
2. Assign a shortcut in **System Settings > Keyboard > Shortcuts > Services**.

---

## Keyboard Maestro

Macro that pops up a prompt box, sends to PromptHub, and pastes the response:

```
1. Trigger: Custom keyboard shortcut
2. Action: Prompt with hidden answer "%Prompt%"
3. Action: Execute shell script:
   curl -s http://localhost:9090/v1/chat/completions \
     -H "Authorization: Bearer sk-prompthub-default-001" \
     -H "Content-Type: application/json" \
     -d "{
       \"model\": \"qwen/qwen3-4b-2507\",
       \"messages\": [{\"role\": \"user\", \"content\": \"%Variable%Prompt%\"}]
     }" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
4. Action: Paste result into front app
```

---

## HTTP Client (Postman / Insomnia)

1. **Method:** `POST`
2. **URL:** `http://localhost:9090/v1/chat/completions`
3. **Headers:**
   ```
   Authorization: Bearer sk-prompthub-default-001
   Content-Type: application/json
   ```
4. **Body (JSON):**
   ```json
   {
     "model": "qwen/qwen3-4b-2507",
     "messages": [
       {"role": "user", "content": "Your prompt here"}
     ]
   }
   ```

---

## Enhancement API

To enhance a prompt without chat completion:

```bash
curl -s http://localhost:9090/llm/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: default" \
  -d '{"prompt": "make a website"}' | python3 -m json.tool
```

Response includes the enhanced prompt, provider (`lm-studio` or `openrouter`), and privacy level.

---

## Responses API (Codex-compatible)

For clients that use the OpenAI Responses API format:

```bash
curl -s http://localhost:9090/v1/responses \
  -H "Authorization: Bearer sk-prompthub-default-001" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3-4b-2507",
    "input": "What is 2 + 2?"
  }'
```

Supports `instructions` (system prompt) and array `input` with message roles.

---

**See also:** [OpenAPI spec](openapi.yaml) for the full endpoint reference.
