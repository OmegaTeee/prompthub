#!/usr/bin/env bash
set -euo pipefail

# Simple release helper for AgentHub
# Usage: ./scripts/release.sh 0.1.1 "Release notes summary"

if [[ "$#" -lt 1 ]]; then
  echo "Usage: $0 <new-version> [release-notes]"
  exit 2
fi

NEW_VERSION=$1
RELEASE_NOTES=${2-""}

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "${ROOT_DIR}"

# Ensure working tree is clean
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree not clean. Commit or stash changes before releasing." >&2
  git status --porcelain
  exit 1
fi

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
echo "Last tag: ${LAST_TAG:-<none>}"

# Generate changelog entry from commits since last tag
if [[ -n "${LAST_TAG}" ]]; then
  LOG=$(git log "${LAST_TAG}..HEAD" --pretty=format:"- %s (%an)")
else
  LOG=$(git log --pretty=format:"- %s (%an)")
fi

DATE=$(date -u +%Y-%m-%d)

TMPFILE=$(mktemp -t agenthub_release)
trap 'rm -f "$TMPFILE"' EXIT
{
  echo "## [${NEW_VERSION}] - ${DATE}"
  if [[ -n "${RELEASE_NOTES}" ]]; then
    echo
    echo "${RELEASE_NOTES}"
  fi
  echo
  if [[ -n "${LOG}" ]]; then
    echo "### Changes"
    echo "${LOG}"
  fi
  echo
  cat CHANGELOG.md
} > "${TMPFILE}"

mv "${TMPFILE}" CHANGELOG.md
git add CHANGELOG.md

# Update pyproject.toml version (robust replacement)
if command -v sed >/dev/null 2>&1; then
  # Prefer perl for a safe in-place edit if available
  if command -v perl >/dev/null 2>&1; then
    perl -pe 's/^(version\s*=\s*)"[^"]+"/$1"'"${NEW_VERSION}"'"/e' -i.bak pyproject.toml
    rm -f pyproject.toml.bak
  else
    # Fallback to awk-based rewrite (POSIX-friendly)
    awk -v new="${NEW_VERSION}" 'BEGIN{q="\""} /^version[[:space:]]*=/ {sub(/"[^"]*"/, q new q)} {print}' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml
  fi
else
  echo "sed not available; please update pyproject.toml version manually." >&2
  exit 1
fi

git add pyproject.toml

# Commit and tag
git commit -m "chore(release): ${NEW_VERSION}" || true
git tag -a "${NEW_VERSION}" -m "Release ${NEW_VERSION}"

git push origin HEAD
git push origin "${NEW_VERSION}"

if command -v gh >/dev/null 2>&1; then
  if [[ -n "${RELEASE_NOTES}" ]]; then
    gh release create "${NEW_VERSION}" -t "${NEW_VERSION}" -n "${RELEASE_NOTES}"
  else
    # Use part of CHANGELOG for release notes if gh supports file import
    gh release create "${NEW_VERSION}" -t "${NEW_VERSION}" --notes-file=CHANGELOG.md
  fi
  echo "Created GitHub release via gh"
else
  echo "gh CLI not found; skipping GitHub release creation. You can create a release manually." >&2
fi

echo "Release ${NEW_VERSION} complete."
