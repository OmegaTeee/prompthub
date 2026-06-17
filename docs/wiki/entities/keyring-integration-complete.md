---
slug: keyring-integration-complete
section: entities
status: documented
---
# Keyring Integration Complete

The keyring integration provides a secure, platform‑native store for
MCP authentication tokens.  By delegating credential storage to the
OS keychain or macOS Keychain, clients avoid exposing secrets in
either environment variables or plain‑text files.

## Implementation
The integration is achieved through the `keyring` Python package,
wrapping the ``mcp-remote`` npm package.  The package is populated
via a small wrapper that authenticates against the system keychain
and forwards the credentials to the remote service.

## Usage
The first run stores the token in the OS store and subsequent
invocations read it automatically.

## Status
All legacy credential files have been removed and the keyring is
now the sole source of truth for authentication.
