# Figma Integration Guide

> **For**: Design-to-code workflows and design system management via AI Agent Hub

---

## Overview

The Figma MCP integration lets you:

- ✅ Extract design specs directly from Figma files
- ✅ Convert designs to HTML/CSS/React code
- ✅ Keep design systems in sync with code
- ✅ Automate design documentation
- ✅ Generate accessibility reports from designs

**Use case:** Designer shares a Figma file → Claude generates production-ready code

---

## Prerequisites

### What You Need

- [ ] Figma account (free tier works)
- [ ] At least one Figma design file
- [ ] Figma API token
- [ ] AI Agent Hub already running (from getting-started.md)

### Get Your Figma API Token

1. Go to **Figma Settings** → **Personal Access Tokens**
2. Click **Create a new token**
3. Name it: `agenthub`
4. Copy the token (long string starting with `fig_`)

**Save it securely:**

```bash
# Store in Keychain (see keychain-setup.md)
security add-generic-password \
  -s "agenthub-figma" \
  -a "default" \
  -w "fig_your-actual-token-here" \
  ~/Library/Keychains/login.keychain-db
```

---

## Installation

### Step 1: Add Figma MCP Server to Router

Edit your router config at `~/.agenthub/config.json`:

```json
{
  "mcp_servers": {
    "figma": {
      "type": "mcp-figma",
      "enabled": true,
      "config": {
        "api_token_keychain": {
          "service": "agenthub-figma",
          "account": "default"
        }
      }
    }
  }
}
```

### Step 2: Restart Router

```bash
launchctl restart com.agenthub.service

# Verify it's running
sleep 3
curl http://localhost:9090/health
```

### Step 3: Test Connection

```bash
# Test Figma access
curl -X POST http://localhost:9090/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "figma_list_files",
    "input": {}
  }'

# Should return list of your Figma files
```

---

## Using Figma Integration

### In Claude Desktop

**Extract design specs:**

```
I have a Figma file at https://www.figma.com/file/abc123/my-design

Can you:
1. List all frames and components
2. Extract color palette
3. Document spacing/sizing rules
```

**Convert to code:**

```
From my Figma file (figma.com/file/abc123/hero-section):
- Convert the hero section to HTML + CSS
- Make it responsive
- Add accessibility attributes
```

**Generate documentation:**

```
Create a design system documentation from my Figma file.
Include:
- Component library
- Color tokens
- Typography scales
- Spacing system
```

### In VS Code (Cline)

```
@figma Read my design system from https://www.figma.com/file/design-system

Generate TypeScript components that match these designs:
- Button component with all variants
- Form input with states
- Card component
```

---

## Troubleshooting

### "Figma API token not found"

**Problem:** Token not stored in Keychain

**Solution:**

```bash
# Re-add the token
security add-generic-password \
  -s "agenthub-figma" \
  -a "default" \
  -w "fig_your-token" \
  ~/Library/Keychains/login.keychain-db
```

### "File Not found" or "Access denied"

**Problem:** Figma URL incorrect or you don't have access

**Solution:**

1. Check the file URL: `https://www.figma.com/file/FILE_ID/file-name`
2. Verify you have edit or view access in Figma
3. Use full URL, not shortened version

---

## See Also

- **getting-started.md** — Initial setup
- **app-configs.md** — Claude/VS Code/Raycast config
- **comfyui-integration.md** — Image generation (pairs with Figma)
- **comparison-table.md** — AI Agent Hub overview
