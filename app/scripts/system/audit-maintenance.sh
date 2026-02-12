#!/bin/bash
#
# Audit Log Maintenance Script
#
# Provides utilities for managing AgentHub audit logs and activity database.
#
# Usage:
#   ./scripts/audit-maintenance.sh [command]
#
# Commands:
#   status      - Show current log sizes and entry counts
#   cleanup     - Remove entries older than 30 days
#   backup      - Create backup of audit logs and activity database
#   rotate      - Force log rotation
#   verify      - Verify log integrity
#   query       - Query audit logs (interactive)

set -euo pipefail

AUDIT_LOG="/tmp/agenthub/audit.log"
ACTIVITY_DB="/tmp/agenthub/activity.db"
ROUTER_URL="http://localhost:9090"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

function log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function check_files() {
    if [[ ! -f "${AUDIT_LOG}" ]]; then
        log_warn "Audit log not found: ${AUDIT_LOG}"
        return 1
    fi

    if [[ ! -f "${ACTIVITY_DB}" ]]; then
        log_warn "Activity database not found: ${ACTIVITY_DB}"
        return 1
    fi

    return 0
}

function cmd_status() {
    log_info "Audit Log Status"
    echo ""

    if [[ -f "${AUDIT_LOG}" ]]; then
        SIZE=$(du -h "${AUDIT_LOG}" | cut -f1)
        LINES=$(wc -l < "${AUDIT_LOG}")
        log_info "Audit Log: ${AUDIT_LOG}"
        echo "  Size: ${SIZE}"
        echo "  Entries: ${LINES}"
        echo ""

        # Show event type distribution
        echo "Event Types:"
        cat "${AUDIT_LOG}" | jq -r '.event' | sort | uniq -c | sort -rn | sed 's/^/  /'
        echo ""
    else
        log_warn "Audit log not found"
    fi

    if [[ -f "${ACTIVITY_DB}" ]]; then
        SIZE=$(du -h "${ACTIVITY_DB}" | cut -f1)
        log_info "Activity Database: ${ACTIVITY_DB}"
        echo "  Size: ${SIZE}"

        # Query database for stats
        if command -v sqlite3 &> /dev/null; then
            TOTAL=$(sqlite3 "${ACTIVITY_DB}" "SELECT COUNT(*) FROM activity")
            echo "  Entries: ${TOTAL}"

            echo ""
            echo "HTTP Methods:"
            sqlite3 "${ACTIVITY_DB}" "SELECT method, COUNT(*) as count FROM activity GROUP BY method ORDER BY count DESC" | sed 's/^/  /' | sed 's/|/ : /'
            echo ""

            echo "Status Codes:"
            sqlite3 "${ACTIVITY_DB}" "SELECT status, COUNT(*) as count FROM activity GROUP BY status ORDER BY status" | sed 's/^/  /' | sed 's/|/ : /'
        fi
    else
        log_warn "Activity database not found"
    fi
}

function cmd_cleanup() {
    log_info "Cleaning up old activity entries (>30 days)..."

    RESPONSE=$(curl -s -X POST "${ROUTER_URL}/audit/activity/cleanup?days=30")

    if echo "${RESPONSE}" | jq -e '.deleted' &> /dev/null; then
        DELETED=$(echo "${RESPONSE}" | jq -r '.deleted')
        log_info "Deleted ${DELETED} old entries"
    else
        log_error "Failed to cleanup: ${RESPONSE}"
        exit 1
    fi
}

function cmd_backup() {
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="/tmp/agenthub/backups"
    mkdir -p "${BACKUP_DIR}"

    log_info "Creating backup..."

    if [[ -f "${AUDIT_LOG}" ]]; then
        AUDIT_BACKUP="${BACKUP_DIR}/audit_${TIMESTAMP}.log.gz"
        gzip -c "${AUDIT_LOG}" > "${AUDIT_BACKUP}"
        log_info "Audit log backed up: ${AUDIT_BACKUP}"
    fi

    if [[ -f "${ACTIVITY_DB}" ]]; then
        ACTIVITY_BACKUP="${BACKUP_DIR}/activity_${TIMESTAMP}.db"
        sqlite3 "${ACTIVITY_DB}" ".backup '${ACTIVITY_BACKUP}'"
        gzip "${ACTIVITY_BACKUP}"
        log_info "Activity DB backed up: ${ACTIVITY_BACKUP}.gz"
    fi

    # Cleanup old backups (keep 30 days)
    find "${BACKUP_DIR}" -name "*.gz" -mtime +30 -delete
    log_info "Old backups cleaned up (>30 days)"
}

function cmd_rotate() {
    log_info "Forcing log rotation..."

    if [[ -f "${AUDIT_LOG}" ]]; then
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        ROTATED="${AUDIT_LOG}.${TIMESTAMP}"
        mv "${AUDIT_LOG}" "${ROTATED}"
        gzip "${ROTATED}"
        log_info "Rotated audit log to: ${ROTATED}.gz"

        # Touch new log file
        touch "${AUDIT_LOG}"
        chmod 644 "${AUDIT_LOG}"
    else
        log_warn "No audit log to rotate"
    fi
}

function cmd_verify() {
    log_info "Verifying audit log integrity..."

    if [[ ! -f "${AUDIT_LOG}" ]]; then
        log_error "Audit log not found"
        exit 1
    fi

    # Check JSON validity
    INVALID=0
    while IFS= read -r line; do
        if ! echo "${line}" | jq empty 2>/dev/null; then
            ((INVALID++))
        fi
    done < "${AUDIT_LOG}"

    if [[ ${INVALID} -eq 0 ]]; then
        log_info "All entries are valid JSON ✓"
    else
        log_error "Found ${INVALID} invalid JSON entries"
        exit 1
    fi

    # Verify database integrity
    if [[ -f "${ACTIVITY_DB}" ]] && command -v sqlite3 &> /dev/null; then
        if sqlite3 "${ACTIVITY_DB}" "PRAGMA integrity_check" | grep -q "ok"; then
            log_info "Database integrity check passed ✓"
        else
            log_error "Database integrity check failed"
            exit 1
        fi
    fi
}

function cmd_query() {
    log_info "Audit Log Query (press Ctrl+C to exit)"
    echo ""

    while true; do
        echo "Query options:"
        echo "  1. Recent events (last 10)"
        echo "  2. Events by client ID"
        echo "  3. Failed operations"
        echo "  4. Credential access"
        echo "  5. Custom jq query"
        echo ""
        read -p "Select option (1-5): " option

        case ${option} in
            1)
                log_info "Recent events:"
                tail -10 "${AUDIT_LOG}" | jq -c '{time: .timestamp[11:19], event: .event, action: .action, resource: .resource_name, status: .status, client: .client_id}'
                ;;
            2)
                read -p "Client ID: " client_id
                log_info "Events by client '${client_id}':"
                cat "${AUDIT_LOG}" | jq -c "select(.client_id == \"${client_id}\") | {time: .timestamp[11:19], event: .event, action: .action, resource: .resource_name, status: .status}"
                ;;
            3)
                log_info "Failed operations:"
                cat "${AUDIT_LOG}" | jq -c 'select(.status == "failed") | {time: .timestamp[11:19], event: .event, action: .action, resource: .resource_name, error: .error, client: .client_id}'
                ;;
            4)
                log_info "Credential access:"
                cat "${AUDIT_LOG}" | jq -c 'select(.event == "credential_access") | {time: .timestamp[11:19], action: .action, credential: .resource_name, status: .status, client: .client_id}'
                ;;
            5)
                read -p "jq filter: " jq_filter
                cat "${AUDIT_LOG}" | jq -c "$jq_filter"
                ;;
            *)
                log_warn "Invalid option"
                ;;
        esac

        echo ""
    done
}

function cmd_help() {
    echo "Audit Log Maintenance Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status      - Show current log sizes and entry counts"
    echo "  cleanup     - Remove entries older than 30 days"
    echo "  backup      - Create backup of audit logs and activity database"
    echo "  rotate      - Force log rotation"
    echo "  verify      - Verify log integrity"
    echo "  query       - Query audit logs (interactive)"
    echo "  help        - Show this help"
}

# Main
COMMAND="${1:-help}"

case $COMMAND in
    status)
        cmd_status
        ;;
    cleanup)
        cmd_cleanup
        ;;
    backup)
        cmd_backup
        ;;
    rotate)
        cmd_rotate
        ;;
    verify)
        cmd_verify
        ;;
    query)
        cmd_query
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        log_error "Unknown command: ${COMMAND}"
        cmd_help
        exit 1
        ;;
esac
