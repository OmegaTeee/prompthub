# System Scripts

System maintenance for PromptHub.

## Scripts

### `audit-maintenance.sh`

Manage audit logs and the activity database at `/tmp/prompthub/`.

```bash
scripts/system/audit-maintenance.sh status    # Log sizes, entry counts, event distribution
scripts/system/audit-maintenance.sh cleanup   # Remove activity entries older than 30 days (via router API)
scripts/system/audit-maintenance.sh backup    # gzip audit log + sqlite backup to /tmp/prompthub/backups/
scripts/system/audit-maintenance.sh rotate    # Force log rotation (mv + gzip, touch new log)
scripts/system/audit-maintenance.sh verify    # Validate JSON lines + sqlite integrity check
scripts/system/audit-maintenance.sh query     # Interactive query menu (recent events, by client, failures, etc.)
```

Requires `jq` and `sqlite3` for full functionality. The `cleanup` command calls the router's `/audit/activity/cleanup` endpoint.
