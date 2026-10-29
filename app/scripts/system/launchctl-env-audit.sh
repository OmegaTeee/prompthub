#!/usr/bin/env bash
# Audit and optionally sync LaunchAgent-visible token environment variables.
#
# Usage:
#   scripts/system/launchctl-env-audit.sh check   # prints prefixes, lengths, hashes; never full values
#   scripts/system/launchctl-env-audit.sh sync
#   scripts/system/launchctl-env-audit.sh unset VAR

set -euo pipefail

MODE="${1:-check}"

fingerprint() {
  local value="$1"
  if [[ -z "$value" ]]; then
    printf "empty"
    return
  fi

  local len="${#value}"
  local prefix="${value:0:4}"
  local digest
  digest="$(printf "%s" "$value" | shasum -a 256 | awk '{print substr($1, 1, 12)}')"
  printf "%s... len=%s sha256:%s" "$prefix" "$len" "$digest"
}

keychain_secret() {
  local service="$1"
  local account="${USER:-$(id -un)}"

  security find-generic-password -a "$account" -s "prompthub:${service}" -w 2>/dev/null \
    || security find-generic-password -a "$account" -s "$service" -w 2>/dev/null \
    || true
}

source_value() {
  local name="$1"
  local service="$2"
  local value source

  value="$(keychain_secret "$service")"
  if [[ -n "$value" ]]; then
    printf "keychain:%s\t%s" "$service" "$value"
    return
  fi

  value="${!service:-}"
  if [[ -n "$value" ]]; then
    printf "shell:%s\t%s" "$service" "$value"
    return
  fi

  value="${!name:-}"
  if [[ -n "$value" ]]; then
    printf "shell:%s\t%s" "$name" "$value"
    return
  fi

  source="missing:${service}"
  printf "%s\t" "$source"
}

launch_value() {
  local name="$1"
  launchctl getenv "$name" 2>/dev/null || true
}

prefix_ok() {
  local value="$1"
  local prefixes="$2"

  [[ -n "$value" ]] || return 1
  IFS=',' read -r -a allowed <<< "$prefixes"
  for prefix in "${allowed[@]}"; do
    [[ "$value" == "$prefix"* ]] && return 0
  done
  return 1
}

status_line() {
  local name="$1"
  local service="$2"
  local prefixes="$3"
  local src lc state="ok"
  local source source_value_text
  src="$(source_value "$name" "$service")"
  source="${src%%$'\t'*}"
  source_value_text="${src#*$'\t'}"
  lc="$(launch_value "$name")"

  if [[ -z "$source_value_text" ]]; then
    state="missing-source"
  elif [[ -z "$lc" ]]; then
    state="missing-launchctl"
  elif [[ "$source_value_text" != "$lc" ]]; then
    state="mismatch"
  elif ! prefix_ok "$lc" "$prefixes"; then
    state="bad-prefix"
  fi

  printf "%-28s %-18s source=%-22s value=%-34s launchctl=%-34s\n" \
    "$name" "$state" "$source" "$(fingerprint "$source_value_text")" "$(fingerprint "$lc")"
}

sync_var() {
  local name="$1"
  local service="$2"
  local prefixes="$3"
  local src source value
  src="$(source_value "$name" "$service")"
  source="${src%%$'\t'*}"
  value="${src#*$'\t'}"

  if [[ -z "$value" ]]; then
    printf "skip %-28s missing Keychain or shell source for %s\n" "$name" "$service"
    return 1
  fi
  if ! prefix_ok "$value" "$prefixes"; then
    printf "skip %-28s source %s has unexpected prefix (%s)\n" "$name" "$source" "$prefixes"
    return 1
  fi

  launchctl setenv "$name" "$value"
  printf "set  %-28s from %-22s %s\n" "$name" "$source" "$(fingerprint "$value")"
}

unset_var() {
  local name="$1"
  launchctl unsetenv "$name"
  printf "unset %s\n" "$name"
}

TOKEN_SPECS=(
  "GITHUB_PAT_TOKEN:GITHUB_PAT:github_pat_,ghp_,gho_"
  "GITHUB_PAT:GITHUB_PAT:github_pat_,ghp_,gho_"
  "GITHUB_PERSONAL_ACCESS_TOKEN:GITHUB_PAT:github_pat_,ghp_,gho_"
  "GITHUB_API_KEY:GITHUB_API_KEY:github_pat_,ghp_,gho_"
  "PH_API_TOKEN:PH_API_TOKEN:sk-prompthub-"
  "OPENAI_API_KEY:PH_API_TOKEN:sk-prompthub-"
  "LM_API_TOKEN:LM_API_TOKEN:sk-"
  "HF_TOKEN:HUGGINGFACE_API_KEY:hf_"
  "HUGGINGFACE_API_KEY:HUGGINGFACE_API_KEY:hf_"
  "OPENROUTER_API_KEY:OPENROUTER_KEY:sk-or-"
)

case "$MODE" in
  check)
    for spec in "${TOKEN_SPECS[@]}"; do
      IFS=':' read -r name service prefixes <<< "$spec"
      status_line "$name" "$service" "$prefixes"
    done
    ;;
  sync)
    failed=0
    for spec in "${TOKEN_SPECS[@]}"; do
      IFS=':' read -r name service prefixes <<< "$spec"
      sync_var "$name" "$service" "$prefixes" || failed=1
    done
    exit "$failed"
    ;;
  unset)
    target="${2:-}"
    if [[ -z "$target" ]]; then
      printf "Usage: %s unset VAR\n" "$0" >&2
      exit 2
    fi
    unset_var "$target"
    ;;
  *)
    printf "Usage: %s [check|sync|unset VAR]\n" "$0" >&2
    exit 2
    ;;
esac
