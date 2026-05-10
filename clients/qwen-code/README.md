# Qwen Code

Repo-managed source of truth for Qwen Code settings.

Single unified `settings.json` lists every provider Qwen Code can route to;
provider switching happens at runtime via the `/model` picker.

## Provider lineup (in `/model` picker order)

| # | Provider                                  | Model id                       | Base URL                       | Auth env             |
| - | ----------------------------------------- | ------------------------------ | ------------------------------ | -------------------- |
| 1 | **PromptHub Router** (default)            | `qwen3-4b-instruct-2507`       | `http://127.0.0.1:9090/v1`     | `PROMPTHUB_API_KEY`  |
| 2 | PromptHub Router · thinking               | `qwen3-4b-thinking-2507`       | `http://127.0.0.1:9090/v1`     | `PROMPTHUB_API_KEY`  |
| 3 | LM Studio Direct · instruct (fallback)    | `qwen3-4b-instruct-2507`       | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 4 | LM Studio Direct · thinking (fallback)    | `qwen3-4b-thinking-2507`       | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 5 | LM Studio Direct · 0.6B (fast)            | `qwen3-0.6b`                   | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 6 | LM Studio Direct · vision                 | `qwen/qwen3-vl-4b`             | `http://127.0.0.1:1234/v1`     | `LM_API_TOKEN`       |
| 7 | LM Studio Direct · Qwen2.5 Coder 3B/7B/14B| `qwen2.5-coder-{3,7,14}b-instruct` | `http://127.0.0.1:1234/v1` | `LM_API_TOKEN`       |
| 8 | OpenRouter · Free Router                  | `openrouter/free`              | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |

`fastModel` = `qwen3-0.6b` via LM Studio direct. Top-level `model.name` =
`qwen3-4b-instruct-2507`, which resolves to **provider 1 (PromptHub Router)**
because of [first-match-by-id ordering](https://github.com/QwenLM/qwen-code/blob/main/docs/users/configuration/model-providers.md)
when multiple providers share an id.

Why both Router and Direct entries for the same model id? Per Qwen Code's docs,
"models within the same authType are uniquely identified by the combination of
`id` + `baseUrl`." Same model, two routes — picker disambiguates by `name`.

LM Studio's JIT loading + keep-warm settings mean naming the same model under
two providers does **not** spawn two instances; the model is loaded once and
served to both routes.

## Files

- `settings.json` — single unified config (replaces the old `settings.direct.json` + `settings.router.json` toggle pair)
- `mcp.json` — standalone MCP block (loaded separately by Qwen Code if `~/.qwen/mcp.json` is symlinked here; the `mcpServers` block in `settings.json` covers it for the primary path)
- `setup.sh` — one-shot symlink installer; no mode argument
- `check.sh` — reports symlink targets, default model, fastModel, and env-var presence
- `uninstall.sh` — removes the live symlinks
- `qwen-cli-help.md` — reference notes for the Qwen CLI

## Live config paths

```text
~/.qwen/settings.json                   ← primary (Qwen Code reads here)
~/.config/qwen-code/settings.json       ← compatibility (older Qwen Code builds)
```

`setup.sh` symlinks both to the in-repo `settings.json`.

## Setup

Set your env vars (sourced from `clients/dotfiles/shell_common.sh` if you use
the dotfiles symlink):

```bash
export LM_API_TOKEN="$(security find-generic-password -s prompthub -a lm_api_token -w)"
export OPENROUTER_API_KEY="$(security find-generic-password -s prompthub -a openrouter_api_key -w)"
export PROMPTHUB_API_KEY="sk-prompthub-qwen-code-001"
```

Install the symlinks:

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

## Provider switching at runtime

Inside Qwen Code:

```text
/model
```

Pick from the list. To set a new default permanently, edit `model.name` in
`settings.json` to match the desired provider's `id` (and reorder providers
if multiple share that `id`, since first-match wins).

## Notes

- `envKey` is the **environment variable name**, not the value. Credentials
  are read from `process.env[envKey]` at runtime; nothing is persisted.
- `LM_API_TOKEN` is PromptHub's canonical local LM Studio token name.
  `LMSTUDIO_API_KEY` works as a backward-compat alias in `Settings`.
- PromptHub Router entries send `X-Client-Name: qwen-code` AND
  `X-Client-ID: qwen-code` — the second is required for audit-context
  scoping (see `reference_audit_context_headers.md`).
- The retired toggle pattern is gone — `settings.direct.json`,
  `settings.router.json`, and the `qwen-code-direct` / `qwen-code-router`
  aliases. If you still have stale symlinks pointing at the deleted files,
  run `./uninstall.sh` followed by `./setup.sh` to refresh.
