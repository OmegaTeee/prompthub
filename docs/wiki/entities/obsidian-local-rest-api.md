# obsidian-local-rest-api

## Summary

Obsidian community plugin (maintainer: Adam Coddington) that exposes a vault as a local REST API on `https://127.0.0.1:27124`. As of v4.x — manifest title now `Local REST API with MCP` — it also hosts an in-process MCP server at `/mcp/`, superseding the standalone `mcp-tools` plugin's externally-spawned binary. The HTTP-MCP endpoint is PromptHub's modern integration point for Obsidian, reachable via [[mcp-remote]] as a stdio shim until the bridge gains direct HTTP transport.

## Details

**Plugin coordinates**

- Plugin ID: `obsidian-local-rest-api` (immutable; tracks the slug used here)
- Manifest title: shifted from `Local REST API` → `Local REST API with MCP` in the 4.x line
- Authority: published by `coddingtonbear` on GitHub; canonical docs at `https://coddingtonbear.github.io/obsidian-local-rest-api/`
- Per-vault install. The user's `~/Vault/Scratch/` has it (v4.1.2 on disk, v4.0.3 running — pending Obsidian restart). The user's `~/Vault/PKB/` does not.

**Endpoints**

- REST: documented in the upstream interactive API docs (link above). Bearer auth.
- MCP: `https://127.0.0.1:27124/mcp/` — added in v4. Same bearer auth scheme.
- TLS: self-signed cert on 27124. Clients need `NODE_TLS_REJECT_UNAUTHORIZED=0` (or to pin the cert) when calling over HTTPS.
- Port 27123 is the HTTP fallback (no TLS). The convention pairs them as 27123/27124.

**Authentication**

The plugin generates a per-vault API key visible in `Settings → Local REST API & MCP Server`. In PromptHub the value is mirrored to the macOS Keychain at:

- `prompthub:obsidian_api_key` — primary bearer token
- `prompthub:obsidian_authentication` — legacy/secondary entry (purpose pre-dates the unified plugin; likely safe to retire after the HTTP migration lands)

`app/configs/mcp-servers.json` resolves both via its `source: "keyring"` env block.

**History of the convergence**

Before v4, two separate community plugins coexisted:

- `obsidian-local-rest-api` — the long-running REST API plugin (REST only)
- `mcp-tools` — a separate plugin that bundled a Go `mcp-server` binary (~60MB) for stdio-based MCP exposure

In the v4 line, Coddington merged the MCP server *into* the REST API plugin's main.js as an in-process route at `/mcp/`. The `mcp-tools` plugin remains installable but is functionally superseded — its binary still works for stdio clients, but the architectural direction is HTTP-MCP via the unified plugin. See [[mcp-stdio-vs-http-transport]] for the architectural framing.

**PromptHub integration today**

- The `obsidian-mcp-tools` entry in `app/configs/mcp-servers.json` is named for the *legacy* plugin and currently spawns its binary at `~/Vault/Scratch/.obsidian/plugins/mcp-tools/bin/mcp-server` (path corrected during the 2026-06-01 hygiene pass — was previously pointing at the wrong vault parent).
- Auto-start with 3 restart attempts; the path correction stopped the auto-start-failure loop that was tripping the circuit breaker on every router boot.
- Pending: migration to `npx mcp-remote@latest https://127.0.0.1:27124/mcp/` with the bearer header, dropping the binary dependency. This is the "preferred" topology going forward and the one captured in the user's earlier `/wiki` decision branch.

**Vault scoping caveat**

The plugin's HTTP server only responds while the *owning* Obsidian instance is running. Closing the Obsidian window unbinds port 27124. The user's PKB vault has no plugin install at all — querying PKB content via MCP would require either (a) installing the plugin in PKB on a different port and registering it as a separate `mcp-servers.json` entry, or (b) using a single umbrella vault. Currently single-vault (Scratch only).

## Related

- [[mcp-stdio-vs-http-transport]] — the architectural distinction that motivates the migration off the deprecated binary
- [[mcp-remote]] — the npm package used as a stdio↔HTTP shim, the bridge of choice until PromptHub's MCP bridge gains direct HTTP transport

## Sources

- `https://github.com/coddingtonbear/obsidian-local-rest-api` — upstream README (MCP Clients section is the canonical setup reference)
- `https://coddingtonbear.github.io/obsidian-local-rest-api/` — interactive API docs
- `~/Vault/Scratch/.obsidian/plugins/obsidian-local-rest-api/manifest.json` — installed plugin manifest (v4.1.2)
- `app/configs/mcp-servers.json` — PromptHub's server registry entry (`obsidian-mcp-tools`)
