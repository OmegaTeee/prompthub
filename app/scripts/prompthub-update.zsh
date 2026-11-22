#!/usr/bin/env zsh
# Update the deployed PromptHub checkout and restart the LaunchAgent daemon.
#
# Safe by default: refuses to run when the update would touch files with local
# edits, or delete files that live client configs symlink to. Run with
# --dry-run first to see the plan.
#
# Usage: prompthub-update.zsh [--dry-run] [--yes] [--no-restart] [--stash]
#                             [--ignore-links] [--rollback] [-h]
#
# Environment overrides:
#   PROMPTHUB_DEPLOY_DIR  deployed checkout (default ~/.local/share/prompthub)
#   PROMPTHUB_BRANCH      branch to deploy (default main)
#   PROMPTHUB_LABEL       LaunchAgent label (default com.prompthub.router)
#   PROMPTHUB_HEALTH_URL  health endpoint (default http://127.0.0.1:9090/health)
#   PROMPTHUB_LINK_ROOTS  colon-separated dirs scanned for symlinks into the
#                         checkout (default: common client config dirs)
#   DATA_DIR              where deploy-history.log is kept (default ~/.prompthub)

set -euo pipefail

SELF="$0"   # inside zsh functions $0 is the function name, so capture it here

DEPLOY_DIR="${PROMPTHUB_DEPLOY_DIR:-$HOME/.local/share/prompthub}"
BRANCH="${PROMPTHUB_BRANCH:-main}"
LABEL="${PROMPTHUB_LABEL:-com.prompthub.router}"
HEALTH_URL="${PROMPTHUB_HEALTH_URL:-http://127.0.0.1:9090/health}"
HEALTH_TIMEOUT=30
HISTORY="${DATA_DIR:-$HOME/.prompthub}/deploy-history.log"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DEFAULT_LINK_ROOTS=(
  "$HOME/Library/LaunchAgents"
  "$HOME/Library/Application Support/Claude"
  "$HOME/Library/Application Support/Code/User"
  "$HOME/Library/Application Support/Code - Insiders/User"
  "$HOME/.claude" "$HOME/.codex" "$HOME/.config" "$HOME/.cursor"
  "$HOME/.lmstudio" "$HOME/.vscode" "$HOME/.vscode-insiders"
)
# Paths that resolve into the checkout. ~/prompthub is the conventional symlink
# to it; ${:a} normalises but does not follow symlinks, so list it explicitly.
DEPLOY_ABS="${DEPLOY_DIR:a}"
CHECKOUT_PREFIXES=("$DEPLOY_ABS/" "$HOME/prompthub/")
# Files whose change between two commits means deps must be reinstalled.
PY_DEPS_FILE='app/requirements.txt'
NPM_DEPS_RE='^mcps/package(-lock)?\.json$'

DRY_RUN=0 ASSUME_YES=0 RESTART=1 STASH=0 IGNORE_LINKS=0 ROLLBACK=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --yes|-y) ASSUME_YES=1 ;;
    --no-restart) RESTART=0 ;;
    --stash) STASH=1 ;;
    --ignore-links) IGNORE_LINKS=1 ;;
    --rollback) ROLLBACK=1 ;;
    -h|--help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

say()  { print -r -- "[PromptHub] $*"; }
warn() { print -r -- "[PromptHub] WARNING: $*" >&2; }
die()  { print -r -- "[PromptHub] ERROR: $*" >&2; exit 1; }
g()    { git -C "$DEPLOY_DIR" "$@"; }

indent()      { sed 's/^/    /'; }                 # stdin -> stdout, indented
# $1 = file; prints its line count with no padding (BSD wc pads with spaces).
count_lines() { wc -l < "$1" | tr -d ' '; }
# Prints the current UTC time as ISO 8601.
now()         { date -u +%FT%TZ; }
# Appends "<timestamp> <args>" as one line to $HISTORY, creating its directory.
log_history() { mkdir -p "${HISTORY:h}"; print -r -- "$(now) $*" >> "$HISTORY"; }

# Predicates over a file listing changed paths, one per line ($1 = that file).
# py matches the whole line literally; npm matches NPM_DEPS_RE.
py_deps_changed()  { grep -qxF "$PY_DEPS_FILE" "$1"; }
npm_deps_changed() { grep -qE "$NPM_DEPS_RE" "$1"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

confirm() {
  (( ASSUME_YES )) && return 0
  [[ -t 0 ]] || die "Not a terminal; re-run with --yes to proceed."
  local reply
  read -r "reply?[PromptHub] $1 [y/N] "
  [[ "$reply" == [yY]* ]]
}

# Reinstall Python/npm deps when the files that pin them changed between $1 and $2.
sync_deps() {
  local changed="$TMP/deps-changed"
  g diff --name-only "$1" "$2" > "$changed"
  if py_deps_changed "$changed"; then
    [[ -x "$DEPLOY_DIR/app/.venv/bin/pip" ]] || die "No venv at $DEPLOY_DIR/app/.venv"
    say "requirements.txt changed: installing Python deps..."
    "$DEPLOY_DIR/app/.venv/bin/pip" install -q -r "$DEPLOY_DIR/app/requirements.txt"
  fi
  if npm_deps_changed "$changed"; then
    say "mcps/package*.json changed: running npm ci..."
    (cd "$DEPLOY_DIR/mcps" && npm ci --no-audit --no-fund --loglevel=error)
  fi
}

restart_and_check() {
  if (( ! RESTART )); then
    say "Skipping restart (--no-restart). Restart later with:"
    say "  launchctl kickstart -k gui/$(id -u)/$LABEL"
    return 0
  fi
  say "Restarting $LABEL..."
  launchctl kickstart -k "gui/$(id -u)/$LABEL"
  local i
  for (( i = 1; i <= HEALTH_TIMEOUT; i++ )); do
    if curl -fsS --max-time 2 "$HEALTH_URL" > /dev/null 2>&1; then
      say "Health check passed after ${i}s."
      return 0
    fi
    sleep 1
  done
  warn "Health check failed after ${HEALTH_TIMEOUT}s ($HEALTH_URL)."
  local errlog
  errlog="$(/usr/libexec/PlistBuddy -c 'Print :StandardErrorPath' "$PLIST" 2>/dev/null || true)"
  if [[ -n "$errlog" && -f "$errlog" ]]; then
    say "Last lines of $errlog:"
    tail -n 30 "$errlog" >&2
  fi
  say "To roll back: $SELF --rollback"
  return 1
}

# Normalise a symlink target to a path relative to the checkout, or "" if outside.
repo_relative() {
  local link="$1" target
  target="$(readlink "$link")"
  [[ "$target" == /* ]] || target="${link:h}/$target"
  target="${target:a}"
  local prefix
  for prefix in "${CHECKOUT_PREFIXES[@]}"; do
    if [[ "$target" == "$prefix"* ]]; then
      print -r -- "${target#$prefix}"
      return
    fi
  done
}

# True if repo path $1 is deleted by the update, or is a directory containing
# a deleted file. Reads the update's deleted-path list from $TMP/deleted.
is_deleted() {
  grep -Fxq "$1" "$TMP/deleted" \
    || awk -v p="$1/" 'index($0, p) == 1 { f = 1; exit } END { exit !f }' "$TMP/deleted"
}

# Print "<link> -> <repo path>" for each symlink under the link roots (and the
# checkout itself) that points at something the update deletes. Roots come from
# PROMPTHUB_LINK_ROOTS (colon-separated) or DEFAULT_LINK_ROOTS; scan depth is 3.
# Needs $TMP/changed and $TMP/deleted to be populated first.
find_broken_links() {
  local -a roots
  if [[ -n "${PROMPTHUB_LINK_ROOTS:-}" ]]; then
    roots=("${(@s/:/)PROMPTHUB_LINK_ROOTS}")
  else
    roots=("${DEFAULT_LINK_ROOTS[@]}")
  fi
  roots+=("$DEPLOY_DIR")
  local root link rel self
  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    find "$root" -maxdepth 3 \( -name node_modules -o -name .venv -o -name .git \) -prune \
      -o -type l -print 2>/dev/null
  done | while IFS= read -r link; do
    rel="$(repo_relative "$link")"
    [[ -n "$rel" ]] || continue
    # A link inside the checkout that the update itself deletes or replaces is fine.
    self="${link#$DEPLOY_ABS/}"
    [[ "$self" != "$link" ]] && grep -Fxq "$self" "$TMP/changed" && continue
    if is_deleted "$rel"; then
      print -r -- "$link -> $rel"
    fi
  done
}

# --- preflight -----------------------------------------------------------
g rev-parse --git-dir > /dev/null 2>&1 || die "$DEPLOY_DIR is not a git checkout"
current="$(g branch --show-current)"
[[ "$current" == "$BRANCH" ]] || die "Deployed checkout is on '${current:-detached HEAD}', expected '$BRANCH'"

# --- rollback ------------------------------------------------------------
if (( ROLLBACK )); then
  [[ -s "$HISTORY" ]] || die "No deploy history at $HISTORY"
  read -r _ts prev new _rest < <(grep -v ' rollback$' "$HISTORY" | tail -n 1)
  head_sha="$(g rev-parse HEAD)"
  [[ "$head_sha" == "$new" ]] || die "HEAD ($head_sha) is not the last deployed commit ($new); roll back by hand."
  say "Rolling back $DEPLOY_DIR: ${new:0:7} -> ${prev:0:7}"
  (( DRY_RUN )) && { say "Dry run: nothing changed."; exit 0; }
  confirm "Proceed with rollback?" || die "Aborted."
  g reset --keep "$prev"   # keeps local edits; refuses if they conflict
  sync_deps "$new" "$prev"
  log_history "$new" "$prev" rollback
  restart_and_check
  exit $?
fi

# --- plan ----------------------------------------------------------------
say "Fetching origin/$BRANCH in $DEPLOY_DIR..."
g fetch --quiet origin "$BRANCH"
old="$(g rev-parse HEAD)"
target="$(g rev-parse "origin/$BRANCH")"

if [[ "$old" == "$target" ]]; then
  say "Already up to date (${old:0:7})."
  exit 0
fi
g merge-base --is-ancestor "$old" "$target" \
  || die "Deployed $BRANCH has commits not on origin/$BRANCH; resolve by hand."

say "Incoming commits:"
g log --oneline --no-decorate "$old..$target" | indent

g diff --no-renames --name-only "$old" "$target" > "$TMP/changed"
g diff --no-renames --name-only --diff-filter=D "$old" "$target" > "$TMP/deleted"
g diff --no-renames --name-only --diff-filter=A "$old" "$target" > "$TMP/added"

blockers=0

# 1. Local edits the update would overwrite.
g status --porcelain=v1 --untracked-files=no | cut -c4- | sed 's/.* -> //' > "$TMP/dirty"
g ls-files --others --exclude-standard > "$TMP/untracked"
grep -Fxf "$TMP/changed" "$TMP/dirty" > "$TMP/overlap" || true
grep -Fxf "$TMP/added" "$TMP/untracked" >> "$TMP/overlap" || true
if [[ -s "$TMP/overlap" ]]; then
  if (( STASH )); then
    warn "$(count_lines "$TMP/overlap") locally edited file(s) overlap the update; they will be stashed and re-applied (conflicts possible)."
  else
    warn "The update touches files with local edits or untracked copies:"
    indent < "$TMP/overlap" >&2
    say "  Commit or back them up first, or re-run with --stash."
    blockers=1
  fi
fi
if [[ -s "$TMP/dirty" ]]; then
  say "$(count_lines "$TMP/dirty") file(s) have local edits in the deployed checkout (kept unless listed above)."
fi

# 2. Live symlinks pointing at files the update deletes.
if (( ! IGNORE_LINKS )) && [[ -s "$TMP/deleted" ]]; then
  find_broken_links > "$TMP/broken"
  if [[ -s "$TMP/broken" ]]; then
    warn "These symlinks point at files the update deletes; their apps would lose config:"
    indent < "$TMP/broken" >&2
    say "  Move those configs out of the checkout first, or re-run with --ignore-links."
    blockers=1
  fi
fi

py_deps_changed "$TMP/changed" && say "Will reinstall Python deps (requirements.txt changed)."
npm_deps_changed "$TMP/changed" && say "Will run npm ci (mcps/package*.json changed)."
(( RESTART )) && say "Will restart $LABEL and wait for $HEALTH_URL."

if (( blockers )); then
  die "Refusing to update. Fix the issues above and re-run."
fi
if (( DRY_RUN )); then
  say "Dry run: no changes made (only 'git fetch' ran)."
  exit 0
fi

# --- apply ---------------------------------------------------------------
confirm "Update ${old:0:7} -> ${target:0:7}?" || die "Aborted."

stashed=0
if (( STASH )) && [[ -s "$TMP/overlap" ]]; then
  g stash push --quiet --include-untracked -m "prompthub-update $(now)"
  stashed=1
  say "Stashed local edits."
fi

g merge --ff-only --quiet "$target"
log_history "$old" "$target"
say "Checkout now at ${target:0:7} (previous ${old:0:7} logged to $HISTORY)."

if (( stashed )); then
  if g stash pop --quiet; then
    say "Re-applied stashed local edits."
  else
    warn "Stash did not re-apply cleanly; stopping before deps install and restart."
    say "  Resolve the conflicts in $DEPLOY_DIR, run 'git stash drop', then re-run"
    say "  this script (it will reinstall deps and restart), or roll back with --rollback."
    exit 1
  fi
fi

sync_deps "$old" "$target"
restart_and_check
