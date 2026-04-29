# Agent manual: npm/pnpm setup helper

This document explains how agent helpers should manage Node toolchains and npm/pnpm settings for developers.

Responsibilities
- Detect developer shell (`$SHELL`) and do not modify dotfiles without creating a backup.
- Prefer non-destructive changes: suggest commands, create scripts under `scripts/` and ask for explicit `run` permission.
- Use `scripts/setup-node-env.sh` to set npm prefix and enable `corepack`/`pnpm`.

Agent actions (recommended)
- Offer `fnm` as the primary node version manager and provide a link/command to install it.
- For global npm prefix changes, create a backup of the affected profile and present the diff to the user before applying.
- For CI changes, add recommended `cache` entries to the CI YAML (GitHub Actions: cache `~/.npm/_cacache`).
- When installing pnpm, prefer `corepack enable` then `corepack prepare pnpm@latest --activate` when Node supports it.

Safety and approvals
- Always show the exact commands and require user confirmation before running scripts that alter profiles or install global packages.
