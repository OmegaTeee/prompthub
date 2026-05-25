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
export MCP_SERVER_FETCH="${HOME}/.local/pipx/venvs/mcp-server-fetch/bin/"

# Active PATH additions
path_prepend "${HOME}/.lmstudio/bin"
path_prepend "${HOME}/.lmstudio/llmster/current"

# Optional PATH additions
# Uncomment only when the tool is installed and you want it available globally.
# path_prepend "${HOME}/.cargo/bin"
# path_prepend "${HOME}/.claude/bin"
# path_prepend "${HOME}/.dotnet/tools"
# path_prepend "/opt/homebrew/opt/python@3/bin"

# -----------------------------------------------------------------------------
# Package manager homes and caches
# -----------------------------------------------------------------------------

export UV_TOOL_DIR="${HOME}/uv-tools"
export UV_CACHE_DIR="${HOME}/uv-cache"

# Optional PNPM setup
# export PNPM_HOME="${HOME}/Library/pnpm"
# path_prepend "${PNPM_HOME}"


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

export CLAUDE_CODE_SSE_PORT="55260"

export LM_API_TOKEN="$(keychain_secret LM_API_TOKEN)"
export LM_KEY_TOKEN="$(keychain_secret LM_KEY_TOKEN)"
export LM_STUDIO_API_BASE="http://127.0.0.1:1234/v1"
export LM_STUDIO_API_KEY="$(keychain_secret LMSTUDIO_API_KEY)"

export OPENAI_API_KEY="$(keychain_secret OPENAI_API_KEY)"
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_MODEL="qwen3-4b-instruct-2507"

export OPENROUTER_KEY="$(keychain_secret OPENROUTER_KEY)"
export OPENROUTER_API_KEY="$(keychain_secret OPENROUTER_KEY)"

# export OPENCLAW_GATEWAY_PORT="18790"
# export OPENCLAW_GATEWAY_URL="http://127.0.0.1:${OPENCLAW_GATEWAY_PORT}"
# export OPENCLAW_GATEWAY_TOKEN="$(keychain_secret OPENCLAW_GATEWAY_TOKEN)"

export CLOUDFLARE_AUTHTOKEN="$(keychain_secret CLOUDFLARE_AUTHTOKEN)"
export CLOUDINARY_API_SECRET="$(keychain_secret CLOUDINARY_API_SECRET)"

export FIGMA_API_KEY="$(keychain_secret FIGMA_API_KEY)"
export GEMINI_API_KEY="$(keychain_secret GEMINI_API_KEY)"
export GITHUB_API_KEY="$(keychain_secret GITHUB_API_KEY)"
# export GITHUB_PAT="$(keychain_secret GITHUB_PAT)"
export GROQ_API_KEY="$(keychain_secret GROQ_API_KEY)"

export HUGGINGFACE_API_KEY="$(keychain_secret HUGGINGFACE_API_KEY)"
export NETLIFY_AUTH_TOKEN="$(keychain_secret NETLIFY_AUTH_TOKEN)"
export NGROK_AUTHTOKEN="$(keychain_secret NGROK_AUTHTOKEN)"
export OLLAMA_API_KEY="$(keychain_secret OLLAMA_API_KEY)"
export PUBLIC_CLOUDINARY_API_KEY="$(keychain_secret PUBLIC_CLOUDINARY_API_KEY)"


# -----------------------------------------------------------------------------
# SuperCoder Agent Settings
# -----------------------------------------------------------------------------

# Default model for everyday coding.
export SUPERCODER_API_KEY="${LM_STUDIO_API_KEY}"
export SUPERCODER_BASE_URL="${LM_STUDIO_API_BASE}"
export SUPERCODER_MODEL="qwen2.5-coder-7b-instruct"

# Quick model presets.
alias supercoder-min='SUPERCODER_MODEL=qwen2.5-coder-3b-instruct supercoder'
alias supercoder-mid='SUPERCODER_MODEL=qwen2.5-coder-7b-instruct supercoder'
alias supercoder-max='SUPERCODER_MODEL=qwen2.5-coder-14b-instruct supercoder'


# -----------------------------------------------------------------------------
# Optional Ollama environment
# -----------------------------------------------------------------------------

# export OLLAMA_HOST="http://127.0.0.1:11434"
# export OLLAMA_MODELS="${HOME}/.ollama/models"
# export OLLAMA_TMPDIR="${HOME}/.ollama/cache"
export OLLAMA_ORIGINS="app://obsidian.md*,chrome-extension://*,*"
export OLLAMA_KV_CACHE_TYPE="q8_0"
export OLLAMA_KEEP_ALIVE=600
export OLLAMA_INVOCATION="${OLLAMA_INVOCATION:-stdin}"
export OLLAMA_FLASH_ATTENTION="1"
export OLLAMA_ENABLE_STREAM="${OLLAMA_ENABLE_STREAM:-true}"
export OLLAMA_DEBUG=1


# -----------------------------------------------------------------------------
# Convenience aliases
# -----------------------------------------------------------------------------

# Shortcuts
alias zsh='source ~/.shell_common.sh && source ~/.zshrc'
alias bash='source ~/.shell_common.sh && source ~/.bashrc'

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
