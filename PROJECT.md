# PromptHub - Local AI Gateway

Local-first AI hub for macOS — central router, prompt enhancement, and desktop integrations.

## Why PromptHub?

PromptHub runs as a single local AI gateway on your Mac that unifies prompt routing, MCP servers, and desktop clients behind one OpenAI-style endpoint. It’s designed for people who live in macOS terminals and editors but want a stable, observable control plane for local and remote models.


## Overview

PromptHub provides a single local router (`localhost:9090`) that:
- Manages MCP servers centrally (configure once, use everywhere)
- Enhances prompts via Ollama before forwarding to AI services
- Provides circuit breakers for graceful degradation
- Caches responses for performance

**Target clients**: Claude, Visual Studio Code, Raycast, Obsidian, ComfyUI

## Project Status

| Phase  | Status       | Description                                                |
|--------|--------------|------------------------------------------------------------|
| Phase 2 | **Complete** | Core router, caching, circuit breakers, Ollama enhancement |
| Phase 2.5 | **Complete** | MCP server management, stdio bridges                        |
| Phase 3 | **Complete** | Desktop integration, config generators, documentation pipeline |
| Phase 4 | **Complete** | HTMX dashboard with real-time monitoring                    |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+ (for MCP servers)
- Docker Desktop or Colima
- Ollama running locally (`ollama serve`)

### Development

```bash
# Create virtual environment (from app/ directory)
cd app
python -m venv .venv && source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install MCP servers (Node.js packages)
cd ../mcps && npm install && cd ..

# Run router
cd app && uvicorn router.main:app --reload --port 9090

# Verify health
curl http://localhost:9090/health
