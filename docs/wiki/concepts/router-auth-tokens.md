# router-auth-tokens

## Summary

PromptHub involves two distinct bearer tokens that are easy to conflate: the **router token** (an `sk-prompthub-<client>-001` value from `api-keys.json`, used to authenticate against the router's `/v1/*` OpenAI-compat endpoints) and the **LM Studio backend token** (`sk-lm-...`, used by the router to reach LM Studio). Only `/v1/*` validates a bearer at all; the rest of the router ignores `Authorization`. Getting the wrong token in the wrong place is the most common source of local-setup friction.

## Details

### Two tokens, two jobs

| Shell var (convention) | What it is | Who checks it |
|---|---|---|
| `PH_API_TOKEN` | PromptHub **router** bearer — an `sk-prompthub-<client>-001` key from `app/configs/api-keys.json` | The router's `/v1/*` endpoints, via `ApiKeyManager` → `ApiKeysRegistry` (port 9090) |
| `LM_API_TOKEN` | LM Studio **backend** API key (`sk-lm-...`); often disabled/inactive in LM Studio | LM Studio directly (port 1234) — ignored entirely when LM Studio auth is off |

Settings resolves the backend token via `AliasChoices("LLM_API_KEY", "LM_API_TOKEN")` from keyring account `lm_api_token`. The two names are vendor-compat aliases for the *same* backend credential — not a second token.

### The auth boundary (the part that surprises people)

Only the router's **`/v1/*`** OpenAI-compat proxy validates a bearer. `/health`, `/servers`, `/tools`, and `/mcp/*` accept any request regardless of `Authorization`. So:

- A client hitting `/v1/chat/completions` with a bad/missing token gets **401**.
- The same bad token against `/mcp/{server}/...` or `/health` works fine — the header is never inspected.

This asymmetry is why a token problem can look intermittent: it only bites the `/v1` surface.

### Pointing tools at the router vs. LM Studio direct

```sh
# Through the router (token is load-bearing):
export OPENAI_BASE_URL="http://127.0.0.1:9090/v1"
export OPENAI_API_KEY="$PH_API_TOKEN"          # must be a real api-keys.json key

# Direct to LM Studio (token ignored when LM Studio auth is disabled):
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
```

Pitfall: if `OPENAI_BASE_URL` points at LM Studio direct (`:1234`) the request "works" with *any* `OPENAI_API_KEY` because LM Studio isn't checking — so a wrong token stays invisible until you switch the base URL to the router (`:9090`), where it suddenly 401s.

### `localhost` vs `127.0.0.1`

Use `127.0.0.1` in client URLs. macOS resolves `localhost` to IPv6 (`::1`), which can miss a server bound only to IPv4.

### The "default" test key

`sk-prompthub-default-001` (client `default`, `enhance=true`) exists specifically for testing and ad-hoc enhancement calls. Tooling that needs to exercise `/v1` without impersonating a real client — e.g. [[../entities/schemathesis]] — should use it.

## Related

- [[../entities/schemathesis]] — fuzzes the router's OpenAPI schema and authenticates with the `default` test key, exercising exactly the `/v1/*` boundary described here.
- [[../entities/obsidian-local-rest-api]] — a parallel case: another local HTTP service with its own bearer (stored under a separate keychain entry), reinforcing why "which token for which service" must be tracked deliberately.

## Sources

- `app/router/openai_compat/auth.py` — `ApiKeyManager` (the only consumer of `api-keys.json`)
- `app/router/config/settings.py` — `AliasChoices("LLM_API_KEY", "LM_API_TOKEN")`, keyring resolution
- `clients/dotfiles/shell_common.sh` — the `PH_API_TOKEN` / `LM_API_TOKEN` export convention
