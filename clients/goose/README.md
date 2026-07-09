# Goose Wrappers

This directory contains the live Goose configuration used by the symlink at
`~/.config/goose/config.yaml`, plus wrapper commands that make provider
switching predictable.

## Files

- `config.yaml`
  Canonical Goose config tracked in this repo.
- `tools-policy.md`
  Top Of Mind policy injected into every Goose turn via
  `GOOSE_MOIM_MESSAGE_FILE`.
- `goose-provider`
  Generic launcher that sets `GOOSE_PROVIDER` and then runs Goose.
- `goose-lmstudio`
  Launch Goose with `GOOSE_PROVIDER=lmstudio`.
- `goose-codex-acp`
  Launch Goose with `GOOSE_PROVIDER=codex-acp`.
- `goose-pi-acp`
  Launch Goose with `GOOSE_PROVIDER=pi-acp`.
- `goose-claude-acp`
  Launch Goose with `GOOSE_PROVIDER=claude-acp`.
- `.goosehints`
  Local hints for Goose behavior in this repo.

## Provider Wrappers

The wrapper scripts avoid hand-editing `config.yaml` just to switch providers.

```bash
clients/goose/goose-lmstudio
clients/goose/goose-codex-acp
clients/goose/goose-pi-acp
clients/goose/goose-claude-acp
```

If your shell loads [clients/dotfiles/shell_common.sh](/Users/visualval/.local/share/prompthub/clients/dotfiles/shell_common.sh),
you also get these aliases:

```bash
goose-lmstudio
goose-codex-acp
goose-pi-acp
goose-claude-acp
```

You can pass normal Goose subcommands through the wrappers:

```bash
goose-codex-acp info --verbose
goose-pi-acp session
goose-claude-acp recipe list
```

## Active Policy

`config.yaml` keeps `lmstudio` as the default `active_provider`, but the policy
file applies across providers.

Current policy split:

- Obsidian note work must use `obsidian-mcp-tools_*`.
- Repo and git work can use shell tools.
- Obsidian note creation must not fall back to raw file writes outside the vault.

## ACP Provider Notes

- Goose's provider name for the `@agentclientprotocol/claude-agent-acp` adapter
  is `claude-acp`, not `claude-agent-acp`.
- `codex-acp`, `pi-acp`, and `claude-acp` are configured as selectable
  providers in `config.yaml`.
- The wrappers only override `GOOSE_PROVIDER`; they do not rewrite the shared
  policy or extension configuration.

## Installed Skills

The Goose config points `skills-mcp` at the repo-local `skills-curated/`
directory. Currently installed from `block/agent-skills`:

- `api-setup`
- `code-review`
- `testing-strategy`

These are lightweight helpers for setup, review, and validation workflows.

## OKF Harness Fit

The Open Knowledge Format helpers under
[clients/vault-writer](/Users/visualval/.local/share/prompthub/clients/vault-writer)
fit Goose best in two places:

1. Recipe input
   Load `OKF-CONVENTIONS.md` before generating project documentation so the
   agent drafts in the expected format.
2. Post-write validation
   Run `okf-validate.py` against changed Markdown files after note generation.

Recommended harness pattern:

- Recipe: inject OKF conventions and the target note/task template.
- Tools policy: require Obsidian note writes to go through vault tools.
- Validation hook: reject generated notes that fail OKF frontmatter checks.

## Known Gap

`clients/vault-writer/vault-goose` still launches Goose with a hard-coded
`openai` provider and does not preload `OKF-CONVENTIONS.md`. If you want Goose
to behave like the OKF-specific Aider wrapper, add either:

- a Goose recipe that injects `OKF-CONVENTIONS.md`, or
- a Goose-specific policy/hook layer that validates note output with
  `okf-validate.py`.
