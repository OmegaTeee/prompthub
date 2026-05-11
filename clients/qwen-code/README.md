# Qwen Code

Repo-managed source of truth for Qwen Code settings.

Single unified `settings.json` lists every provider Qwen Code can route to;
provider switching happens at runtime via the `/model` picker.

## Provider lineup (in `/model` picker order)

Each provider entry has `name` set to match `id` — the human-readable label
lives in `description`. See [Why `name` = `id`](#why-name--id) below for the
rationale.

| # | Routes via            | id (= `name`)                   | Base URL                       | Auth env             |
| - | --------------------- | ------------------------------- | ------------------------------ | -------------------- |
| 1 | **PromptHub Router**  | `qwen3-4b-instruct-2507`        | `http://127.0.0.1:9090/v1`     | `PROMPTHUB_API_KEY`  |
| 2 | PromptHub Router      | `qwen3-4b-thinking-2507`        | `http://127.0.0.1:9090/v1`     | `PROMPTHUB_API_KEY`  |
| 3 | LM Studio Direct      | `qwen3-0.6b`                    | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 4 | LM Studio Direct      | `qwen/qwen3-vl-4b`              | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 5 | LM Studio Direct      | `qwen2.5-coder-3b-instruct`     | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 6 | LM Studio Direct      | `qwen2.5-coder-7b-instruct`     | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 7 | LM Studio Direct      | `qwen2.5-coder-14b-instruct`    | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 8 | OpenRouter            | `openrouter/free`               | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |

`fastModel` = `qwen3-0.6b` via LM Studio direct. Top-level `model.name` =
`qwen3-4b-instruct-2507` resolves to **provider 1 (PromptHub Router)**.

PromptHub Router only proxies the two Qwen3-4b text models (`-instruct-2507`
and `-thinking-2507`); requests for any other model id flow direct to LM Studio
(`qwen3-0.6b`, vision, Qwen2.5 Coder lineup) or out to OpenRouter
(`openrouter/free`). The router doesn't need to be a passthrough for everything
— it only sits in the path of the models you want enhancement / audit / MCP
injection on.

## Why `name` = `id`

Some Qwen Code clients (notably the VS Code Companion at the time of writing)
send the provider's **`name`** field as the `model` parameter in API requests,
not the `id`. By keeping `name` identical to `id`, the config is robust to
which field a client picks — every request reaches the upstream API with a
valid model id that LM Studio or OpenRouter can resolve.

Tradeoffs accepted:

- `/model` picker shows the bare id (`qwen3-4b-instruct-2507`) rather than a
  friendlier label (`"PromptHub Router · Qwen3 4B Instruct 2507"`). To
  compensate, the route and full description live in the `description` field,
  visible when hovering an entry in the picker or via `/model info`.
- We can't have two provider entries with the same `id` + different `baseUrl`
  (the picker would show two visually identical lines). PR-#27's earlier draft
  included LM Studio Direct fallbacks for the two Router models; those were
  dropped because (a) the picker UX broke and (b) PromptHub Router already
  does its own cloud fallback via OpenRouter, so the LM Studio Direct
  duplication wasn't earning its keep.

LM Studio's JIT loading + keep-warm settings mean naming the same model under
two providers does **not** spawn two instances; the model is loaded once and
served to both routes.

## Files

- `settings.json` — single unified config (replaces the old `settings.direct.json` + `settings.router.json` toggle pair)
- `mcp.json` — standalone MCP block (the `mcpServers` block in `settings.json` covers the primary path)
- `setup.sh` — one-shot **copy** installer (auto-backs-up any existing live file); no mode argument
- `check.sh` — reports drift between repo and live, default model, fastModel, and env-var presence
- `uninstall.sh` — removes the live config files
- `qwen-cli-help.md` — reference notes for the Qwen CLI

## Live config paths

```text
~/.qwen/settings.json                   ← primary (Qwen Code reads here)
~/.config/qwen-code/settings.json       ← compatibility (older Qwen Code builds)
```

`setup.sh` **copies** the in-repo `settings.json` to both paths (with timestamped
backup of any prior live file). Earlier versions used symlinks, but Qwen Code
persists state in-place on `/model` switch / `/auth` etc., so a symlink would
let those writes clobber the repo source. Copy semantics keep the repo file
canonical: re-running `setup.sh` resets the live file to repo state, with the
prior live file preserved as `<target>.bak-<timestamp>`.

To pull live edits back into the repo (review carefully first):

```bash
cp ~/.qwen/settings.json clients/qwen-code/settings.json
git diff clients/qwen-code/settings.json   # review what Qwen Code rewrote
```

## Setup

Required shell env vars — these should already be in `~/.shell_common.sh` if
you use the dotfiles. The critical one is `PROMPTHUB_API_KEY`:

```bash
# Bearer token for the local PromptHub router — not a secret, just an identifier
# that maps to the qwen-code entry in app/configs/api-keys.json.
export PROMPTHUB_API_KEY="sk-prompthub-qwen-code-001"

# These come from Keychain. PromptHub stores entries as service="prompthub:<key>"
# with account=$USER (see app/router/keyring_manager.py for the convention).
export LM_API_TOKEN="$(security find-generic-password -s "prompthub:lm_api_token" -a "$USER" -w)"
export OPENROUTER_API_KEY="$(security find-generic-password -s "prompthub:openrouter_api_key" -a "$USER" -w)"
```

Why explicit shell exports rather than relying on settings.json's `env` block?
Qwen Code's OpenAI SDK reads credentials from `process.env[envKey]` at request
time. The settings.json `env` block is supposed to populate `process.env` but
its loading order vs. SDK init isn't reliable — explicit shell exports remove
the dependency on internal init order.

Install the live config:

```bash
./clients/qwen-code/setup.sh
# or via the alias from clients/dotfiles/shell_common.sh:
qwen-code-setup
```

Verify:

```bash
./clients/qwen-code/check.sh
# or:
qwen-code-check
```

`check.sh` reports each live file as **in sync with repo**, **DRIFTED from repo**
(Qwen Code rewrote it — re-run `setup.sh` to reset), or **missing**.

## Provider switching at runtime

Inside Qwen Code:

```text
/model
```

Pick from the list. To set a new default permanently, edit `model.name` in
`settings.json` to match the desired provider's `id` (and reorder providers
if multiple share that `id`, since first-match wins).

## Notes

- `envKey` is the **environment variable name**, not the value. Qwen Code
  reads the actual credential from `process.env[envKey]` at runtime; secrets
  are not persisted in `settings.json`.
- The exception is `PROMPTHUB_API_KEY = "sk-prompthub-qwen-code-001"` in the
  top-level `env` block — this is intentionally repo-tracked because it's
  not a secret. It's a local-only bearer token issued by the PromptHub
  router at `localhost:9090`, identifying which entry in `app/configs/api-keys.json`
  to apply. Sensitive credentials (`LM_API_TOKEN`, `OPENROUTER_API_KEY`)
  are sourced from the user's environment via `${VAR}` interpolation.
- `LM_API_TOKEN` is PromptHub's canonical local LM Studio token name.
  `LMSTUDIO_API_KEY` works as a backward-compat alias in `Settings`.
- PromptHub Router entries send `X-Client-Name: qwen-code` AND
  `X-Client-ID: qwen-code` — the second is required for audit-context
  scoping (see `reference_audit_context_headers.md`).
- The retired toggle pattern is gone — `settings.direct.json`,
  `settings.router.json`, and the `qwen-code-direct` / `qwen-code-router`
  aliases. If you still have stale symlinks pointing at the deleted files,
  run `./uninstall.sh` followed by `./setup.sh` to refresh.
