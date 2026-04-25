## npm & pnpm setup and recommended workflow

This guide covers recommended setup for a modern macOS developer using Node.js, npm, and pnpm.

Step 1 — Move npm global prefix to a user-writable path

Run the helper script:

```sh
./scripts/setup-node-env.sh
```

This will set your npm prefix to `~/.local/share/npm`, add it to your shell profile, enable corepack, and install `pnpm`.

Step 2 — Per-project `.npmrc`

Use the provided `.npmrc.template` as a starting point. Copy it into your project root as `.npmrc` and customize scopes or registry overrides as needed.

Step 3 — Prefer pnpm for local installs (optional)

Install pnpm via `corepack` or `npm` and use `pnpm install`. pnpm uses a content-addressable store and saves disk/IO for monorepos.

Step 4 — Hygiene tasks

Use `scripts/npm-hygiene.sh` for cache verify, clean, and audit tasks.

Step 5 — CI

In CI prefer `npm ci` or `pnpm install --frozen-lockfile`. Cache `~/.npm/_cacache` or pnpm store between runs.
