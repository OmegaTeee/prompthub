# ComfyUI Integration Guide

> **For**: AI image generation workflows via AI Agent Hub

---

## Overview

ComfyUI + AI Agent Hub lets you:

- ✅ Generate AI images from text prompts
- ✅ Control generation parameters (model, steps, sampler, etc.)
- ✅ Chain image generation with design workflows
- ✅ Automate batch image creation
- ✅ Fine-tune prompts based on outputs

**Use case:** "Generate 5 product variations based on my design specs"

---

## Prerequisites

### What You Need

- [ ] ComfyUI installed on your Mac
- [ ] At least one image generation model (Stable Diffusion, SDXL, etc.)
- [ ] Sufficient GPU/VRAM (8GB+ recommended)
- [ ] AI Agent Hub already running

### Check If ComfyUI Is Installed

```bash
# ComfyUI usually runs on port 8188
curl http://localhost:8188/api/status

# If it responds with JSON, ComfyUI is ready
# If not, install it first:
git clone https://github.com/comfyanonymous/ComfyUI ~/ComfyUI
cd ~/ComfyUI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Installation

### Step 1: Configure Router to Access ComfyUI

Edit `~/.agenthub/config.json`:

```json
{
  "mcp_servers": {
    "comfyui": {
      "type": "mcp-comfyui",
      "enabled": true,
      "config": {
        "comfyui_url": "http://localhost:8188",
        "workflows_dir": "~/.agenthub/comfyui-workflows",
        "output_dir": "~/Desktop/ComfyUI-Output"
      }
    }
  }
}
```

### Step 2: Create Workflow Directory

```bash
mkdir -p ~/.agenthub/comfyui-workflows
mkdir -p ~/Desktop/ComfyUI-Output
```

### Step 3: Restart Router

```bash
launchctl restart com.agenthub.service

# Verify
sleep 3
curl http://localhost:9090/health
```

### Step 4: Test Connection

```bash
# Test ComfyUI access
curl -X POST http://localhost:9090/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "comfyui_list_models",
    "input": {}
  }'

# Should return list of available models
```

---

## Using ComfyUI Integration

### In Claude Desktop

#### Generate Image from Prompt

```
Generate an image using ComfyUI:
- Prompt: "a sleek modern chair, product photography, studio lighting"
- Model: SDXL 1.0
- Sampling steps: 30
- Sampler: DPM++ 2M Karras
- CFG scale: 7.5
- Size: 1024x1024

Save the output and describe what was created.
```

---

## See Also

- **getting-started.md** — Initial AI Agent Hub setup
- **app-configs.md** — Configure Claude/VS Code
- **figma-integration.md** — Design extraction (pairs with ComfyUI)
- **comparison-table.md** — AI Agent Hub overview
