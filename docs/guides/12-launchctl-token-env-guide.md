# Launchctl Token Environment Guide

GUI-launched macOS apps do not always inherit the same shell environment that
Terminal sessions see. This matters for tools launched from VS Code, Codex,
ChatWise, Finder, or the Dock when they need token variables such as
`GITHUB_PAT_TOKEN`.

PromptHub includes a small audit helper for checking and syncing those token
variables without printing the secrets themselves:

```bash
scripts/system/launchctl-env-audit.sh check
scripts/system/launchctl-env-audit.sh sync
scripts/system/launchctl-env-audit.sh unset GITHUB_PAT_TOKEN
```

## Check Current State

Run:

```bash
scripts/system/launchctl-env-audit.sh check
```

The command compares shell/Keychain-backed token sources against the current
GUI-session `launchctl` environment. It prints only token source, prefix,
length, and a short digest.

Use this when a GUI app cannot see a token that works in Terminal.

## Sync Tokens for GUI Apps

Run:

```bash
scripts/system/launchctl-env-audit.sh sync
```

Then fully restart the affected app so it launches with the updated
`launchctl` environment.

## Clear a Bad Token

Run:

```bash
scripts/system/launchctl-env-audit.sh unset GITHUB_PAT_TOKEN
```

Then run `check` again before restarting the affected app.

## Common Pitfalls

- Updating shell startup files does not update already-running GUI apps.
- Restarting a router or server does not refresh a client app's environment.
- `launchctl` values can outlive the shell session that originally set them.
- Token aliases differ by tool; Codex MCP tools expect `GITHUB_PAT_TOKEN`,
  while Claude Code commonly uses `GITHUB_PERSONAL_ACCESS_TOKEN`.
