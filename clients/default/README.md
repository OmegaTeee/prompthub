# Default

Fallback bridge config for unrecognized clients. Also serves as the
**starter boilerplate directory** for new client setup work, including the
copy-paste workflow used before running the client-setup skill on a new branch.

## Files in this directory

- `mcp.json` — Default bridge config (minimal SERVERS filter)
- `setup.sh` — Template: creates symlink from app config location to repo config
- `uninstall.sh` — Template: removes symlink and restores backup

## Adding a new client

```bash
# 1. Create the client directory
mkdir -p clients/<name>

# 2. Copy the default boilerplate
cp clients/default/setup.sh clients/<name>/setup.sh
cp clients/default/uninstall.sh clients/<name>/uninstall.sh

# 3. Edit both scripts — customize the three variables at the top:
#    CLIENT_NAME  — your client's name
#    CONFIG_FILE  — which file in this directory to link
#    APP_CONFIG   — where the app expects to find it

# 4. Add your client's config files (mcp.json, etc.)

# 5. Test
./clients/<name>/setup.sh        # install
./clients/<name>/uninstall.sh    # reverse
```

## Strategies

| Strategy | When to use | Example |
|---|---|---|
| **symlink** | App reads a standalone JSON config file | LM Studio, Claude Desktop |
| **manual** | App uses shared settings (JSONC, mixed config) | Zed, `cherry-studio` |
| **merge** | App config has both MCP and non-MCP sections | _(future)_ |

For `manual` strategy clients, `setup.sh` prints paste instructions instead of
creating symlinks. See `clients/zed/setup.sh` for an example.

Treat this folder as the repo's default starter template. Copy it into the
client-config iteration branch first, then customize it before invoking any
client-specific setup workflow.
