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
# Tool locations and PATH extensions
# -----------------------------------------------------------------------------

export MAGICK_HOME="/opt/homebrew"
export AUTOTRACE="/opt/homebrew/bin/autotrace"
export MPC_SERVER_FETCH="${HOME}/.local/pipx/venvs/mcp-server-fetch/bin/"
export MCP_OBSIDIAN_TOOLS="${HOME}/.local/bin/mcp-obsidian-tools"
export MPC_BRIDGE="${HOME}/.local/share/prompthub/mcps/prompthub-bridge.js"


# Active PATH additions
path_append "${MCP_BRIDGE}"
path_append "${HOME}/.lmstudio/bin"
path_append "${HOME}/.lmstudio/llmster/current"

# Comet Browser (Perplexity/Comet)
path_prepend "/Applications/Comet.app/Contents/MacOS"
path_prepend "${HOME}/Applications/Comet.app/Contents/MacOS"

# Optional PATH additions
# Uncomment only when the tool is installed and you want it available globally.
# path_prepend "${HOME}/.cargo/bin"
# path_prepend "${HOME}/.claude/bin"
# path_prepend "${HOME}/.dotnet/tools"
path_prepend "/opt/homebrew/opt/python@3/bin"

# -----------------------------------------------------------------------------
# Package manager homes and caches
# -----------------------------------------------------------------------------

export UV_TOOL_DIR="${HOME}/uv-tools"
export UV_CACHE_DIR="${HOME}/uv-cache"

# PNPM setup (shared across shells)
export PNPM_HOME="${HOME}/Library/pnpm"
path_prepend "${PNPM_HOME}/bin"


# -----------------------------------------------------------------------------
# Local ML / GPU settings
# -----------------------------------------------------------------------------

export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.8


# -----------------------------------------------------------------------------
# Local services and shell hooks
# -----------------------------------------------------------------------------

# Colima: auto-start when working inside the configured project directory.
export PROJECT_FOLDER="${HOME}/code/"  # <-- Adjust this to your actual project folder

start_colima_if_needed() {
  if [[ "$PWD" == *"$PROJECT_FOLDER"* ]]; then
    colima start >/dev/null 2>&1 || true
  fi
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

export GITHUB_API_KEY="$(keychain_secret GITHUB_API_KEY)"
export GITHUB_PAT="$(keychain_secret GITHUB_PAT)"
export GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PAT}" # <-- Claude Code expect this specific variable name

# PromptHub (PH) Project: Reverse Proxy Router, Local MPC Server, and Tools Management Bridge
export LM_API_TOKEN="$(keychain_secret LM_API_TOKEN)" # <-- Inactive LM Studio Token
export PH_API_TOKEN="$(keychain_secret PH_API_TOKEN)" # <-- Active PromptHub-Router Token
export PH_HF_TOKEN="$(keychain_secret HUGGINGFACE_API_KEY)"
export PH_ROUTER_URL="http://127.0.0.1:9090"
export PH_DAEMON_MODEL="qwen3-4b-instruct-2507" # <-- always-on runs from the router (TBD: switch to Qwopus3.5 v3)

# Hugging Face --> Used for fetching models and calling Hugging Face APIs directly (e.g. for embeddings)
export HUGGINGFACE_API_KEY="${PH_HF_TOKEN}"
export HF_TOKEN="${PH_HF_TOKEN}"

# OpenAI-compatible Endpoints --> PH Router to LM Studio (or other providers)
export OPENAI_API_KEY="${PH_API_TOKEN}"
export OPENAI_BASE_URL="http://127.0.0.1:9090/v1"
export OPENAI_MODEL="${PH_DAEMON_MODEL}"

# OpenRouter --> PH cloud fallback testing
export OPENROUTER_API_KEY="$(keychain_secret OPENROUTER_KEY)"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export OPENROUTER_MODEL="openrouter/free"

# LM Studio --> Direct Local Connection to LLM Host Provider (bypassing the router; used for testing and fallback)
export LM_STUDIO_API_KEY="$(keychain_secret LMSTUDIO_API_KEY)"
export LM_STUDIO_API_URL="http://127.0.0.1:1234/v1"
export LM_STUDIO_MODEL="${PH_DAEMON_MODEL}"

# Ollama MacOS App --> Alternative Local LLM Host Provider
# export OLLAMA_HOST="http://127.0.0.1:11434"
# export OLLAMA_MODELS="${HOME}/.ollama/models"
# export OLLAMA_TMPDIR="${HOME}/.ollama/cache"
export OLLAMA_API_KEY="$(keychain_secret OLLAMA_API_KEY)"
export OLLAMA_ORIGINS="chrome-extension://*,app://*,https://*"
export OLLAMA_INVOCATION="${OLLAMA_INVOCATION:-stdin}"
export OLLAMA_ENABLE_STREAM="${OLLAMA_ENABLE_STREAM:-true}"
export OLLAMA_FLASH_ATTENTION="1"
export OLLAMA_KV_CACHE_TYPE="q8_0"
export OLLAMA_KEEP_ALIVE="1800"
export OLLAMA_NUM_PARALLEL="1" # Raise to 2 for 7B–14B models
export OLLAMA_MAX_LOADED_MODELS="1"
export OLLAMA_DEBUG="0"

# OpenClaw
export OPENCLAW_GATEWAY_TOKEN="$(keychain_secret OPENCLAW_GATEWAY_TOKEN)"
export OPENCLAW_CONFIG_PATH="${HOME}/.openclaw/config.json"

# Alternative AI Providers
export MISTRAL_API_KEY="$(keychain_secret MISTRAL_API_KEY)"
export GEMINI_API_KEY="$(keychain_secret GEMINI_API_KEY)"
# export GROQ_API_KEY="$(keychain_secret GROQ_API_KEY)"

# Other Hosting service tokens (only set these if you use them in your projects)
export CLOUDFLARE_AUTHTOKEN="$(keychain_secret CLOUDFLARE_AUTHTOKEN)"
export PUBLIC_CLOUDINARY_API_KEY="$(keychain_secret PUBLIC_CLOUDINARY_API_KEY)"
export CLOUDINARY_API_SECRET="$(keychain_secret CLOUDINARY_API_SECRET)"
export NETLIFY_AUTH_TOKEN="$(keychain_secret NETLIFY_AUTH_TOKEN)"
# export NGROK_AUTHTOKEN="$(keychain_secret NGROK_AUTHTOKEN)"

# Optional API keys for tools (uncomment if you use them in your workflows)
# export FIGMA_API_KEY="$(keychain_secret FIGMA_API_KEY)"


# -----------------------------------------------------------------------------
# Convenience aliases
# -----------------------------------------------------------------------------

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
prompthub-keys() {
  (cd "${HOME}/prompthub/app" && source .venv/bin/activate && python scripts/manage-keys.py "$@")
}
