#!/bin/zsh
# shellcheck shell=bash
# ~/.zshrc
#
# Interactive Zsh configuration:
# - Homebrew environment
# - shared shell settings
# - prompt, completions, and interactive tooling

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# -----------------------------------------------------------------------------
# Core environment
# -----------------------------------------------------------------------------

# Let Homebrew manage its own PATH-related environment.
eval "$(/opt/homebrew/bin/brew shellenv)"

# Shared login-style env
# [ -f "${HOME}/.profile" ] && source "${HOME}/.profile"

# Shared shell settings (aliases, PNPM, Qwen, functions, etc.)
[ -f "${HOME}/.shell_common.sh" ] && source "${HOME}/.shell_common.sh"

# Keep PATH and FPATH unique in interactive Zsh sessions.
typeset -U path fpath

# Set NODE_PATH so global npm modules are available to ad hoc Node scripts.
export NODE_PATH="$(npm root -g)"

# Load direnv for per-directory environment management.
eval "$(direnv hook zsh)"


# -----------------------------------------------------------------------------
# Prompt and terminal integration
# -----------------------------------------------------------------------------

[ -f "${HOME}/.iterm2_shell_integration.zsh" ] && source "${HOME}/.iterm2_shell_integration.zsh"


source "$(brew --prefix)/share/powerlevel10k/powerlevel10k.zsh-theme"
[ -f "${HOME}/.p10k.zsh" ] && source "${HOME}/.p10k.zsh"


# -----------------------------------------------------------------------------
# Completions
# -----------------------------------------------------------------------------

if type brew &>/dev/null; then
  FPATH=$(brew --prefix)/share/zsh-completions:$FPATH
fi

fpath+=~/.zfunc
autoload -Uz compinit
compinit


# -----------------------------------------------------------------------------
# Tool integrations
# -----------------------------------------------------------------------------

# if command -v ngrok &>/dev/null; then
#   eval "$(ngrok completion)"
# fi

[[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code -- --locate-shell-integration-path zsh)"

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh


# OpenClaw Completion
[ -f "/Users/visualval/.openclaw/completions/openclaw.zsh" ] && source "/Users/visualval/.openclaw/completions/openclaw.zsh"

# pnpm
export PNPM_HOME="/Users/visualval/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME/bin:"*) ;;
  *) export PATH="$PNPM_HOME/bin:$PATH" ;;
esac
# pnpm end
