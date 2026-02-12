# System Scripts

Scripts for system-level operations like audit log management and SIEM integration.

## Scripts

### `audit-maintenance.sh`
Manages audit log rotation, compression, archival, and integrity verification.

**Purpose:** Automated maintenance of PromptHub's audit logging system with tamper detection.

**Usage:**
```bash
# Run full maintenance
scripts/system/audit-maintenance.sh

# Rotate logs only
scripts/system/audit-maintenance.sh --rotate

# Compress archived logs
scripts/system/audit-maintenance.sh --compress

# Verify log integrity
scripts/system/audit-maintenance.sh --verify

# Clean old archives (30+ days)
scripts/system/audit-maintenance.sh --clean

# Generate audit report
scripts/system/audit-maintenance.sh --report

# Run in dry-run mode
scripts/system/audit-maintenance.sh --dry-run
```

**Operations:**
1. **Rotation**: Rotates logs when size exceeds threshold
2. **Compression**: gzip compression of rotated logs
3. **Integrity**: SHA256 checksum verification
4. **Archival**: Moves old logs to archive directory
5. **Cleanup**: Deletes logs older than retention period

**Example output:**
```
🗂️  PromptHub Audit Log Maintenance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Current Status:
  • Active log: audit.log (128 MB)
  • Rotated logs: 15 files (2.3 GB)
  • Archive age: 0-45 days
  • Integrity: ✓ All checksums valid

🔄 Rotating logs...
  • audit.log → audit.log.2024-01-30
  • Created new audit.log
  ✓ Rotation complete (1.2s)

📦 Compressing rotated logs...
  • audit.log.2024-01-30 → audit.log.2024-01-30.gz
  • Saved 89% (114 MB → 12 MB)
  ✓ Compression complete (3.4s)

🔐 Verifying integrity...
  • audit.log.2024-01-29.gz: ✓
  • audit.log.2024-01-28.gz: ✓
  • audit.log.2024-01-27.gz: ✓
  ✓ All checksums valid

🧹 Cleaning old archives...
  • Deleted 3 logs older than 30 days
  • Freed 245 MB
  ✓ Cleanup complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Maintenance complete
Next run: 2024-01-31 00:00
```

**Configuration:**
```bash
# Environment variables
export AUDIT_LOG_DIR="${HOME}/.local/share/prompthub/logs"
export AUDIT_RETENTION_DAYS=30
export AUDIT_MAX_SIZE_MB=100
export AUDIT_COMPRESSION=true
export AUDIT_INTEGRITY_CHECK=true
```

**Cron schedule:**
```cron
# Run daily at midnight
0 0 * * * /Users/user/.local/share/prompthub/scripts/system/audit-maintenance.sh

# Run weekly for deep verification
0 2 * * 0 /Users/user/.local/share/prompthub/scripts/system/audit-maintenance.sh --verify
```

**Dependencies:**
- `bash` 4.0+
- `gzip` for compression
- `sha256sum` or `shasum` for integrity
- `jq` for JSON parsing

### `siem-forwarder.sh`
Forwards audit events to SIEM systems (Splunk, ELK, Datadog, etc.) in real-time.

**Purpose:** Stream PromptHub audit logs to external security information and event management systems.

**Usage:**
```bash
# Start forwarder (background daemon)
scripts/system/siem-forwarder.sh start

# Stop forwarder
scripts/system/siem-forwarder.sh stop

# Check status
scripts/system/siem-forwarder.sh status

# Test connection
scripts/system/siem-forwarder.sh test

# Manual forward (one-time)
scripts/system/siem-forwarder.sh forward --file logs/audit.log

# Configure endpoint
scripts/system/siem-forwarder.sh config --endpoint https://siem.company.com/ingest
```

**Supported SIEM systems:**
- **Splunk** - HTTP Event Collector (HEC)
- **ELK Stack** - Elasticsearch HTTP API
- **Datadog** - Log ingestion API
- **Azure Sentinel** - Log Analytics API
- **AWS CloudWatch** - PutLogEvents API
- **Generic webhook** - Custom JSON POST

**Example output:**
```
🚀 SIEM Forwarder for PromptHub
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📡 Configuration:
  • Endpoint: https://splunk.company.com:8088/services/collector
  • Format: Splunk HEC
  • Batch size: 100 events
  • Flush interval: 30s
  • Retry attempts: 3

▶️  Starting forwarder...
  • PID: 12345
  • Log: logs/siem-forwarder.log
  • Watching: logs/audit.log
  ✓ Forwarder running

📤 Forwarding events...
  [12:34:56] Sent 47 events (batch 1)
  [12:35:26] Sent 23 events (batch 2)
  [12:35:56] Sent 91 events (batch 3)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 161 events forwarded successfully
❌ 0 events failed
```

**Configuration file:**
```json
// configs/siem-forwarder.json
{
  "enabled": true,
  "endpoint": "https://siem.company.com/ingest",
  "format": "splunk",  // or "elk", "datadog", "generic"
  "auth": {
    "type": "bearer",
    "token": "HEC-TOKEN-FROM-KEYCHAIN"
  },
  "batch_size": 100,
  "flush_interval_seconds": 30,
  "retry_attempts": 3,
  "retry_delay_seconds": 5,
  "filters": {
    "event_types": ["credential_access", "admin_action", "security_alert"],
    "min_severity": "warning"
  }
}
```

**Event format:**
```json
{
  "timestamp": "2024-01-30T12:34:56.789Z",
  "event_type": "credential_access",
  "severity": "info",
  "request_id": "uuid-1234",
  "client_id": "claude-desktop",
  "client_ip": "127.0.0.1",
  "action": "get",
  "credential_key": "obsidian_api_key",
  "status": "success",
  "source": "prompthub",
  "environment": "production"
}
```

**Dependencies:**
- `bash` 4.0+
- `curl` for HTTP requests
- `jq` for JSON processing
- `tail` for log watching

## Audit Log Management

### Log Structure

```
logs/
├── audit.log                      # Active audit log
├── audit.log.2024-01-30           # Rotated (today)
├── audit.log.2024-01-29.gz        # Compressed (yesterday)
├── audit.log.2024-01-28.gz        # Archived
├── audit-checksums.txt            # Integrity checksums
└── siem-forwarder.log             # Forwarder activity
```

### Integrity Verification

```bash
# Generate checksums
scripts/system/audit-maintenance.sh --generate-checksums

# Verify all logs
scripts/system/audit-maintenance.sh --verify

# Manual verification
sha256sum logs/audit.log.2024-01-30.gz
grep "audit.log.2024-01-30.gz" logs/audit-checksums.txt
```

### Log Queries

```bash
# Security alerts in last 24 hours
jq 'select(.event_type == "security_alert" and .timestamp > "2024-01-29")' logs/audit.log

# Failed credential access
jq 'select(.event_type == "credential_access" and .status == "failed")' logs/audit.log

# Admin actions by user
jq 'select(.event_type == "admin_action" and .client_id == "admin")' logs/audit.log

# Anomaly detection events
jq 'select(.anomaly_detected == true)' logs/audit.log
```

## SIEM Integration

### Splunk Setup

```bash
# 1. Create HEC token in Splunk
# Settings → Data Inputs → HTTP Event Collector → New Token

# 2. Add token to Keychain
security add-generic-password -a $USER -s "splunk_hec_token" -w "YOUR-HEC-TOKEN"

# 3. Configure forwarder
cat > configs/siem-forwarder.json << EOF
{
  "enabled": true,
  "endpoint": "https://splunk.company.com:8088/services/collector",
  "format": "splunk",
  "auth": {
    "type": "hec",
    "token_keychain_key": "splunk_hec_token"
  }
}
EOF

# 4. Start forwarder
scripts/system/siem-forwarder.sh start
```

### ELK Stack Setup

```bash
# 1. Configure Elasticsearch endpoint
cat > configs/siem-forwarder.json << EOF
{
  "enabled": true,
  "endpoint": "https://elasticsearch.company.com:9200/prompthub-audit/_doc",
  "format": "elk",
  "auth": {
    "type": "basic",
    "username": "elastic",
    "password_keychain_key": "elasticsearch_password"
  }
}
EOF

# 2. Create index template
curl -X PUT "elasticsearch.company.com:9200/_index_template/prompthub-audit" \
  -H "Content-Type: application/json" \
  -d @configs/elasticsearch-template.json

# 3. Start forwarder
scripts/system/siem-forwarder.sh start
```

### Custom Webhook

```bash
# Configure generic webhook
cat > configs/siem-forwarder.json << EOF
{
  "enabled": true,
  "endpoint": "https://your-webhook.com/ingest",
  "format": "generic",
  "auth": {
    "type": "bearer",
    "token_keychain_key": "webhook_token"
  },
  "headers": {
    "X-Source": "prompthub",
    "X-Environment": "production"
  }
}
EOF
```

## Monitoring & Alerts

### Health Checks

```bash
# Check audit system health
curl http://localhost:9090/audit/health

# Check SIEM forwarder status
scripts/system/siem-forwarder.sh status

# Verify log rotation
ls -lh logs/audit.log*

# Check disk usage
du -sh logs/
```

### Alert Rules

```bash
# Alert on failed credential access (3+ in 5 min)
jq -s 'map(select(.event_type == "credential_access" and .status == "failed")) |
       group_by(.credential_key) |
       map(select(length >= 3)) |
       length' logs/audit.log

# Alert on security alerts
jq 'select(.event_type == "security_alert")' logs/audit.log | wc -l

# Alert on disk space (>80%)
df -h logs/ | awk 'NR==2 {if ($5+0 > 80) print "ALERT: Disk usage " $5}'
```

### LaunchAgent Monitoring

```xml
<!-- ~/Library/LaunchAgents/com.prompthub.audit-monitor.plist -->
<dict>
  <key>Label</key>
  <string>com.prompthub.audit-monitor</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/user/.local/share/prompthub/scripts/system/audit-maintenance.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>0</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>RunAtLoad</key>
  <true/>
</dict>
```

## Compliance & Reporting

### Generate Audit Report

```bash
# Generate monthly report
scripts/system/audit-maintenance.sh --report --month 2024-01

# Output: reports/audit-2024-01.html
```

**Report includes:**
- Total events by type
- Security alerts summary
- Failed access attempts
- Admin actions audit trail
- Credential access patterns
- Top active clients
- Anomaly detection summary

### Compliance Logs

```bash
# Export for compliance (SOC 2, HIPAA, etc.)
scripts/system/audit-maintenance.sh --export-compliance \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --format json \
  --output compliance-2024-01.json

# Include integrity proof
scripts/system/audit-maintenance.sh --export-compliance \
  --include-checksums \
  --sign-with-gpg
```

## Troubleshooting

### Log Rotation Issues

**Problem:** Logs not rotating despite size threshold

**Solution:**
```bash
# Manual rotation
scripts/system/audit-maintenance.sh --force-rotate

# Check cron job
crontab -l | grep audit-maintenance

# Test rotation
echo "test" >> logs/audit.log
scripts/system/audit-maintenance.sh --rotate --verbose
```

### SIEM Forwarding Failures

**Problem:** Events not reaching SIEM

**Diagnosis:**
```bash
# Test SIEM endpoint
scripts/system/siem-forwarder.sh test

# Check forwarder logs
tail -f logs/siem-forwarder.log

# Manual event send
curl -X POST "https://siem.company.com/ingest" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"test": "event"}'
```

**Solution:**
```bash
# Verify credentials
security find-generic-password -a $USER -s "splunk_hec_token" -w

# Restart forwarder
scripts/system/siem-forwarder.sh restart

# Check firewall rules
nc -zv siem.company.com 8088
```

### Integrity Verification Failed

**Problem:** Checksum mismatch detected

**Response:**
```bash
# 1. Identify tampered log
scripts/system/audit-maintenance.sh --verify --verbose

# 2. Investigate changes
diff <(sha256sum logs/audit.log.2024-01-30.gz) \
     <(grep "audit.log.2024-01-30.gz" logs/audit-checksums.txt)

# 3. Alert security team
python3 -c "from router.audit import audit_security_alert; \
            audit_security_alert('tampered_audit_log', \
                                details={'file': 'audit.log.2024-01-30.gz'})"

# 4. Restore from backup (if available)
cp backups/audit.log.2024-01-30.gz.backup logs/audit.log.2024-01-30.gz
```

## Advanced Usage

### Custom Log Filters

```bash
# Filter by severity
jq 'select(.severity == "critical")' logs/audit.log > critical-events.json

# Filter by time range
jq 'select(.timestamp >= "2024-01-30T00:00:00Z" and
           .timestamp <= "2024-01-30T23:59:59Z")' logs/audit.log

# Complex filter
jq 'select(.event_type == "credential_access" and
           .status == "failed" and
           .client_ip != "127.0.0.1")' logs/audit.log
```

### Automated Remediation

```bash
# auto-remediate.sh
#!/bin/bash
# Respond to security events

EVENT=$(jq -r '.event_type' <<< "$1")

case "$EVENT" in
  "repeated_failures")
    # Block IP temporarily
    echo "Blocking IP $CLIENT_IP"
    pfctl -t blocked_ips -T add "$CLIENT_IP"
    ;;
  "credential_probing")
    # Rotate compromised credential
    python3 scripts/security/manage-keys.py --rotate "$KEY_NAME"
    ;;
esac
```

## Related Documentation

- [Audit System](../../docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md)
- [Security Alerts](../../router/security_alerts.py)
- [Compliance Guide](../../docs/compliance.md)
