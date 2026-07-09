#!/bin/sh

# =============================================================================
# Shared shell configuration
# Intended to be sourced by interactive Bash and Zsh sessions.
# Keep active settings near the top and optional examples commented out below.
# =============================================================================

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

# Read a secret from the macOS Keychain.
# Returns an empty string when the secret is missing so shell startup still works.
keychain_secret() {
  security find-generic-password -a "${USER}" -s "$1" -w 2>/dev/null || echo ""
}

# Prepend a directory to PATH if it exists and is not already present.
path_prepend() {
  [ -d "$1" ] || return 0
  case ":${PATH}:" in
    *:"$1":*) ;;
    *) PATH="$1:${PATH}" ;;
  esac
}

# Append a directory to PATH if it exists and is not already present.
path_append() {
  [ -d "$1" ] || return 0
  case ":${PATH}:" in
    *:"$1":*) ;;
    *) PATH="${PATH}:$1" ;;
  esac
}


# -----------------------------------------------------------------------------
# Tool, Package managers and PATH extensions
# -----------------------------------------------------------------------------
# export MCP_SERVER_FETCH="${HOME}/.local/pipx/venvs/mcp-server-fetch/bin/"
# export MCP_BRIDGE="${HOME}/.local/bin/mcp-bridge"
# export MCP_OBSIDIAN_TOOLS="${HOME}/.local/bin/mcp-obsidian-tools"

export MAGICK_HOME="/opt/homebrew"
export AUTOTRACE="/opt/homebrew/bin/autotrace"

# UV Tools (local LLM tools and utilities)
export UV_TOOL_DIR="${HOME}/uv-tools"
export UV_CACHE_DIR="${HOME}/uv-cache"

# PyTorch MPS (Metal GPU) settings for macOS
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.8

# LM Studio (local LLM host and tools)
path_prepend "${HOME}/.lmstudio/bin"
path_prepend "${HOME}/.lmstudio/llmster/current"

# Python 3 (Homebrew)
path_prepend "/opt/homebrew/opt/python@3/bin"

# Comet Browser (Perplexity/Comet)
path_prepend "/Applications/Comet.app/Contents/MacOS"
path_prepend "${HOME}/Applications/Comet.app/Contents/MacOS"

# PNPM
export PNPM_HOME="${HOME}/Library/pnpm"
path_prepend "${PNPM_HOME}/bin"


# Hermes Agent — ensure ~/.local/bin is on PATH
export PATH="$HOME/.local/bin:$PATH"

# Node.js and NPM
path_prepend "${HOME}/.npm-global/bin"

# Bun (JavaScript runtime and package manager)
path_prepend "${HOME}/.bun/bin"

# VLLM (local LLM inference engine)
path_prepend "${HOME}/.venv-vllm-metal/bin"

# Headroom (local LLM proxy)
export HEADROOM_PROXY_URL="http://127.0.0.1:8787"
export HEADROOM_HOME="${HOME}/.local/share/prompthub/headroom"
path_prepend "${HEADROOM_HOME}/.venv/bin"



# Optional: make OpenAI-style tools default to Headroom proxy
export OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1"
export OPENAI_API_BASE="${HEADROOM_PROXY_URL}/v1"
export OPENAI_API_KEY="${PH_API_TOKEN:-lm-studio}"

# Optional Anthropic-style defaults through Headroom
export ANTHROPIC_BASE_URL="${HEADROOM_PROXY_URL}/v1"
export COPILOT_PROVIDER_TYPE="${COPILOT_PROVIDER_TYPE:-anthropic}"
export COPILOT_PROVIDER_BASE_URL="${HEADROOM_PROXY_URL}/v1"
export ENABLE_TOOL_SEARCH="${ENABLE_TOOL_SEARCH:-true}"



# -----------------------------------------------------------------------------
# Local services and shell hooks
# -----------------------------------------------------------------------------

# Colima: auto-start when working inside the configured project directory.
export PROJECT_FOLDER="${HOME}/code/"  # <-- Adjust this to your actual project folder

start_colima_if_needed() {
  case "$PWD" in
    *"$PROJECT_FOLDER"*) colima start >/dev/null 2>&1 || true ;;
  esac
}

# Only install the directory-change hook in Zsh.
if [ -n "${ZSH_VERSION:-}" ]; then
  autoload -U add-zsh-hook
  add-zsh-hook chpwd start_colima_if_needed
fi

start_colima_if_needed

# Optional Docker socket override for Colima
# export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"



# -----------------------------------------------------------------------------
# Secrets from Keychain + Local API endpoints and ports
# -----------------------------------------------------------------------------

GITHUB_API_KEY="$(keychain_secret GITHUB_API_KEY)"
export GITHUB_API_KEY
GITHUB_PAT="$(keychain_secret GITHUB_PAT)"
export GITHUB_PAT
export GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PAT}" # <-- Claude Code expects this
export GITHUB_PAT_TOKEN="${GITHUB_PAT}" # <-- Codex MCP tools expect this

# PromptHub (PH) Project: Reverse Proxy Router, Local MPC Server, and Tools Management Bridge
LM_API_TOKEN="$(keychain_secret LM_API_TOKEN)" # <-- Inactive LM Studio Token
export LM_API_TOKEN
PH_API_TOKEN="$(keychain_secret PH_API_TOKEN)" # <-- Active PromptHub-Router Token
export PH_API_TOKEN
export PH_ROUTER_URL="http://127.0.0.1:9090"
export PH_DAEMON_MODEL="qwen3-4b-instruct-2507" # <-- always-on runs from the router

# Hugging Face --> Used for fetching models and calling Hugging Face APIs directly (e.g. for embeddings)
HUGGINGFACE_API_KEY="$(keychain_secret HUGGINGFACE_API_KEY)"
export HUGGINGFACE_API_KEY
export HF_TOKEN="${HUGGINGFACE_API_KEY}"
export HF_HUB_CACHE="${HOME}/.cache/huggingface/hub"

# OpenAI-compatible Endpoints --> PH Router LM Studio (or other providers)
export OPENAI_API_KEY="${PH_API_TOKEN}"
export OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1" # <-- PromptHub router remains shared default; Headroom opt-in via wrappers
export OPENAI_MODEL="${PH_DAEMON_MODEL}"

# OpenRouter --> PH cloud fallback testing
OPENROUTER_API_KEY="$(keychain_secret OPENROUTER_KEY)"
export OPENROUTER_API_KEY
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export OPENROUTER_MODEL="openrouter/free"

# LM Studio --> Direct Local Connection to LLM Host Provider (bypassing the router; used for testing and fallback)
LM_STUDIO_API_KEY="$(keychain_secret LMSTUDIO_API_KEY)"
export LM_STUDIO_API_KEY
export LMSTUDIO_TOKEN="${LM_STUDIO_API_KEY}"
export LM_STUDIO_API_URL="http://127.0.0.1:1234/v1"
export LM_STUDIO_MODEL="${PH_DAEMON_MODEL}"

# Ollama MacOS App --> Alternative Local LLM Host Provider
OLLAMA_API_KEY="$(keychain_secret OLLAMA_API_KEY)"
export OLLAMA_API_KEY
export OLLAMA_ORIGINS="chrome-extension://*,app://*,https://*"
export OLLAMA_INVOCATION="${OLLAMA_INVOCATION:-stdin}"
export OLLAMA_ENABLE_STREAM="${OLLAMA_ENABLE_STREAM:-true}"
export OLLAMA_NUM_PARALLEL="2" # Raise to 2 for 7B–14B models
export OLLAMA_MAX_LOADED_MODELS="3"
export OLLAMA_KV_CACHE_TYPE="q8_0"
export OLLAMA_KEEP_ALIVE="1800"
export OLLAMA_FLASH_ATTENTION="1"
# export OLLAMA_DEBUG="0"

# OpenClaw
# export OPENCLAW_LIVE_ACP_BIND_AGENT="claude"
OPENCLAW_GATEWAY_TOKEN="$(keychain_secret OPENCLAW_GATEWAY_TOKEN)"
export OPENCLAW_GATEWAY_TOKEN
export OPENCLAW_CONFIG_PATH="${HOME}/.openclaw/openclaw.json"
export OPENCLAW_DIST="${HOME}/.npm-global/lib/node_modules/openclaw/dist"

# Discord-channel
DISCORD_BOT_API_KEY="$(keychain_secret DISCORD_BOT_API_KEY)"
export DISCORD_BOT_API_KEY

#Discord Llmcord Bot
DISCORD_BOT_TOKEN="$(keychain_secret DISCORD_BOT_TOKEN)"
export DISCORD_BOT_TOKEN
DISCORD_CLIENT_ID="$(keychain_secret DISCORD_CLIENT_ID)"
export DISCORD_CLIENT_ID

# Parallel-web Search MCP
PARALLEL_API_KEY="$(keychain_secret PARALLEL_API_KEY)"
export PARALLEL_API_KEY

# Alternative AI Providers
GROQ_API_KEY="$(keychain_secret GROQ_API_KEY)"
export GROQ_API_KEY
MISTRAL_API_KEY="$(keychain_secret MISTRAL_API_KEY)"
export MISTRAL_API_KEY
GEMINI_API_KEY="$(keychain_secret GEMINI_API_KEY)"
export GEMINI_API_KEY
export PI_ACP_ENABLE_EMBEDDED_CONTEXT=true

# Other Hosting service tokens (only set these if you use them in your projects)
# export NGROK_AUTHTOKEN="$(keychain_secret NGROK_AUTHTOKEN)"
# Optional API keys for tools (uncomment if you use them in your workflows)
# export FIGMA_API_KEY="$(keychain_secret FIGMA_API_KEY)"

CLOUDFLARE_AUTHTOKEN="$(keychain_secret CLOUDFLARE_AUTHTOKEN)"
export CLOUDFLARE_AUTHTOKEN

PUBLIC_CLOUDINARY_API_KEY="$(keychain_secret PUBLIC_CLOUDINARY_API_KEY)"
export PUBLIC_CLOUDINARY_API_KEY

CLOUDINARY_API_SECRET="$(keychain_secret CLOUDINARY_API_SECRET)"
export CLOUDINARY_API_SECRET

NETLIFY_AUTH_TOKEN="$(keychain_secret NETLIFY_AUTH_TOKEN)"
export NETLIFY_AUTH_TOKEN



# -----------------------------------------------------------------------------
# Convenience aliases
# -----------------------------------------------------------------------------

# Headroom helpers
headroom_proxy() {
  launchctl kickstart -k "gui/$(id -u)/com.prompthub.headroom"
}
headroom_doctor() {
  headroom doctor --port "${HEADROOM_PORT:-8787}" "$@"
}
headroom_codex() {
  launchctl kickstart -k "gui/$(id -u)/com.prompthub.headroom" >/dev/null 2>&1 || true
  codex "$@"
}
headroom_claude() {
  ANTHROPIC_BASE_URL="${HEADROOM_PROXY_URL}/v1" \
  OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1" \
  headroom wrap claude "$@"
}
headroom_openai() {
  OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1" \
  OPENAI_API_KEY="${OPENAI_API_KEY:-${PH_API_TOKEN:-lm-studio}}" \
  "$@"
}

hdiff() { headroom diff "$@"; }
hloc()  { headroom loc "$@"; }
hsg()   { headroom sg  "$@"; }


# Optional: Set environment variables for local LLM inference engines (llama.cpp, vllm, etc.)
export LLAMA_ARG_FLASH_ATTN=1
export LLAMA_ARG_CACHE_TYPE_K=q8_0
export LLAMA_ARG_CACHE_TYPE_V=q8_0
export LLAMA_ARG_THREADS=10
export LLAMA_ARG_THREADS_BATCH=10
export GGML_METAL_NO_RESIDENCY=1

export LLAMA_CACHE="${HOME}/.cache/llama.cpp"
export LLAMA_CPP_HOME="${HOME}/llama.cpp"
path_prepend "${LLAMA_CPP_HOME}/build/bin"

alias llama-server='${LLAMA_CPP_HOME}/build/bin/llama-server'
alias llama-cli='${LLAMA_CPP_HOME}/build/bin/llama-cli'
alias llama-bench='${LLAMA_CPP_HOME}/build/bin/llama-bench'
alias llama-simple='${LLAMA_CPP_HOME}/build/bin/llama-simple'

# Shortcuts
alias load-zsh='source ~/.shell_common.sh && source ~/.zshrc'
alias load-bash='source ~/.shell_common.sh && source ~/.bashrc'

# Local image generation helper
alias imagine='python ~/comfyui/user/scripts/ollama_drawthings_generate.py'

# PromptHub development shortcuts
alias prompthub-router='launchctl kickstart -k gui/$(id -u)/com.prompthub.router'
alias prompthub-router-stop='launchctl bootout gui/$(id -u)/com.prompthub.router'
alias prompthub-health='curl http://localhost:9090/health'
alias prompthub-logs='tail -f ~/prompthub/logs/router-stderr.log'

# Keyring CLI (app/scripts/manage-keys.py with venv auto-activated; subshell so the venv doesn't leak)
prompthub_keys() {
  (cd "${HOME}/prompthub/app" && . .venv/bin/activate && python scripts/manage-keys.py "$@")
}

# --- vault-writer: local-model OKF doc agents (default vault: ~/Vault/Scratch; pass --llm for ~/Vault/LLM) ---
alias vault-goose='${HOME}/prompthub/clients/vault-writer/vault-goose'
alias vault-aider='${HOME}/prompthub/clients/vault-writer/vault-aider'
alias vault-codex='${HOME}/prompthub/clients/vault-writer/vault-codex'
alias goose-lmstudio='${HOME}/prompthub/clients/goose/goose-lmstudio'
alias goose-codex-acp='${HOME}/prompthub/clients/goose/goose-codex-acp'
alias goose-pi-acp='${HOME}/prompthub/clients/goose/goose-pi-acp'
alias goose-claude-acp='${HOME}/prompthub/clients/goose/goose-claude-acp'
