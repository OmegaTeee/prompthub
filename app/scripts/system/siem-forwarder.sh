#!/bin/bash
#
# SIEM Log Forwarder
#
# Forwards AgentHub audit logs to SIEM platforms.
# Supports: Splunk, ELK/Elastic, Datadog, generic syslog
#
# Usage:
#   ./scripts/siem-forwarder.sh <platform> [options]
#
# Platforms:
#   splunk     - Forward to Splunk HEC (HTTP Event Collector)
#   elastic    - Forward to Elasticsearch
#   datadog    - Forward to Datadog Logs
#   syslog     - Forward to syslog server

set -euo pipefail

AUDIT_LOG="/tmp/agenthub/audit.log"

function usage() {
    echo "SIEM Log Forwarder for AgentHub"
    echo ""
    echo "Usage: $0 <platform> [options]"
    echo ""
    echo "Platforms:"
    echo "  splunk <HEC_URL> <HEC_TOKEN>  - Forward to Splunk HEC"
    echo "  elastic <ES_URL> <INDEX>      - Forward to Elasticsearch"
    echo "  datadog <DD_API_KEY>          - Forward to Datadog"
    echo "  syslog <SYSLOG_HOST>          - Forward to syslog server"
    echo ""
    echo "Examples:"
    echo "  $0 splunk https://splunk.example.com:8088/services/collector ABC123"
    echo "  $0 elastic https://elastic.example.com:9200 agenthub-audit"
    echo "  $0 datadog abc123def456"
    echo "  $0 syslog syslog.example.com:514"
}

function forward_to_splunk() {
    HEC_URL="$1"
    HEC_TOKEN="$2"

    echo "[INFO] Forwarding to Splunk HEC: ${HEC_URL}"

    # Read audit log and send each line to Splunk
    while IFS= read -r line; do
        curl -k -X POST "${HEC_URL}" \
            -H "Authorization: Splunk ${HEC_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "{\"event\": ${line}, \"sourcetype\": \"agenthub:audit\"}" \
            --silent --show-error

        echo "." # Progress indicator
    done < "${AUDIT_LOG}"

    echo ""
    echo "[INFO] Forwarding complete"
}

function forward_to_elastic() {
    ES_URL="$1"
    INDEX="$2"

    echo "[INFO] Forwarding to Elasticsearch: ${ES_URL}/${INDEX}"

    # Read audit log and bulk index to Elasticsearch
    while IFS= read -r line; do
        # Elasticsearch bulk API format
        echo "{\"index\":{\"_index\":\"${INDEX}\"}}"
        echo "${line}"
    done < "${AUDIT_LOG}" | curl -X POST "${ES_URL}/_bulk" \
        -H "Content-Type: application/x-ndjson" \
        --data-binary @- \
        --silent --show-error

    echo ""
    echo "[INFO] Forwarding complete"
}

function forward_to_datadog() {
    DD_API_KEY="$1"
    DD_URL="https://http-intake.logs.datadoghq.com/v1/input"

    echo "[INFO] Forwarding to Datadog Logs"

    # Read audit log and send to Datadog
    while IFS= read -r line; do
        # Add hostname and service tags
        event=$(echo "${line}" | jq -c ". + {\"ddsource\": \"agenthub\", \"service\": \"audit\", \"hostname\": \"$(hostname)\"}")

        curl -X POST "${DD_URL}/${DD_API_KEY}" \
            -H "Content-Type: application/json" \
            -d "${event}" \
            --silent --show-error

        echo "." # Progress indicator
    done < "${AUDIT_LOG}"

    echo ""
    echo "[INFO] Forwarding complete"
}

function forward_to_syslog() {
    SYSLOG_HOST="$1"

    echo "[INFO] Forwarding to syslog: ${SYSLOG_HOST}"

    # Use logger or netcat to send to syslog
    if command -v logger &> /dev/null; then
        while IFS= read -r line; do
            logger -n "${SYSLOG_HOST}" -P 514 -t agenthub "${line}"
        done < "${AUDIT_LOG}"
    else
        echo "[ERROR] logger command not found"
        exit 1
    fi

    echo "[INFO] Forwarding complete"
}

# Main
if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

PLATFORM="$1"

case "${PLATFORM}" in
    splunk)
        if [[ $# -ne 3 ]]; then
            echo "[ERROR] Usage: $0 splunk <HEC_URL> <HEC_TOKEN>"
            exit 1
        fi
        forward_to_splunk "$2" "$3"
        ;;
    elastic)
        if [[ $# -ne 3 ]]; then
            echo "[ERROR] Usage: $0 elastic <ES_URL> <INDEX>"
            exit 1
        fi
        forward_to_elastic "$2" "$3"
        ;;
    datadog)
        if [[ $# -ne 2 ]]; then
            echo "[ERROR] Usage: $0 datadog <DD_API_KEY>"
            exit 1
        fi
        forward_to_datadog "$2"
        ;;
    syslog)
        if [[ $# -ne 2 ]]; then
            echo "[ERROR] Usage: $0 syslog <SYSLOG_HOST>"
            exit 1
        fi
        forward_to_syslog "$2"
        ;;
    *)
        echo "[ERROR] Unknown platform: ${PLATFORM}"
        usage
        exit 1
        ;;
esac
