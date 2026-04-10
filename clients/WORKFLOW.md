# Client Config Workflow

How to iterate on client configurations without polluting `main`, and how to promote a stable slice into a reviewable PR.

## Why this workflow exists

Client configurations (`clients/*/mcp.json`, `settings.json`, presets, prompt templates, `llm.txt` files, etc.) are continuously tweaked as you:

- Try new MCP servers in a client's `SERVERS` list
- Adjust LM Studio presets for different model sizes
- Update VS Code settings when a new extension appears
- Rewrite prompt templates after testing

These edits happen far more often than "code ships to production" moments. If each tweak landed directly on `main`, the commit history would become 90% config churn. If each tweak needed its own PR, you'd spend more time writing PR descriptions than iterating.

The compromise is a **long-running branch** for experimental config work, combined with **short-lived PR branches** for stable slices you want to ship.

## Branch topology

```text
main                              stable, all merged PRs, protected
├── wip/client-config-iteration   long-running, continuous config tweaks
└── feature/<client>-config       short-lived, one per "stable slice" PR
```

- `main` — never commit directly; everything lands via PR
- `wip/client-config-iteration` — your personal iteration space; commit freely
- `feature/<client>-config` — created on demand when a client's configuration stabilizes; merges into main; deleted after merge

The WIP branch **never merges directly into main**. Instead, you extract stable slices into fresh PR branches. This keeps `main` history clean while letting you iterate at your own pace.

## Day-to-day workflow

### Starting a config session

Always switch to the WIP branch before editing any file under `clients/`:

```bash
git checkout wip/client-config-iteration
git pull origin wip/client-config-iteration   # sync if you work from multiple machines
```

### Making edits

Edit files normally in your editor. Some clients (like LM Studio) auto-write to files in `clients/<name>/` — that's fine, the changes will show up in `git status` on the WIP branch.

### Committing

Commit frequently with descriptive messages scoped to one client per commit when possible:

```bash
git add clients/lm-studio/config-presets/
git commit -m "tweak(lm-studio): lower temperature on Research preset"

git add clients/vscode/settings.json
git commit -m "tweak(vscode): enable format-on-save for markdown"
```

**Why one client per commit**: When you later extract a stable slice, `git log -- clients/<name>/` gives you a clean list of commits to cherry-pick. Mixed commits make extraction messier.

### Pushing

Push to origin so the WIP branch is backed up and accessible from other machines:

```bash
git push
```

No PR needed. The branch lives perpetually.

## Promoting a stable slice to a PR

When a client's configuration is working well and you want to lock it in on `main`, extract it into a fresh PR branch. **Use Strategy 1 (path-scoped checkout) by default** — it produces one clean commit per client and matches how config iteration actually works. Strategy 2 is documented as a fallback for rare cases where commit history needs to be preserved.

### Strategy 1: Path-scoped checkout (default — use this)

**Best when**: You want one clean commit on main with the current state of a client's folder, regardless of how many commits it took to get there on WIP.

**How it works**: `git checkout <branch> -- <path>` copies the current contents of files at a given path from another branch into your working tree. No commit history is carried over; you write a single fresh commit on the PR branch.

```bash
# 1. Start from fresh main
git checkout main
git pull origin main

# 2. Create a feature branch
git checkout -b feature/lm-studio-config-stable

# 3. Pull in the current state of the client folder from WIP
git checkout wip/client-config-iteration -- clients/lm-studio/

# 4. Review what got staged
git status
git diff --cached clients/lm-studio/

# 5. Commit as a single atomic change
git commit -m "feat(lm-studio): stable client configuration

Snapshot of clients/lm-studio/ from wip/client-config-iteration
after iteration on presets and prompt templates."

# 6. Push and open PR
git push -u origin feature/lm-studio-config-stable
gh pr create --base main --title "feat: stable LM Studio client configuration"
```

**Trade-off**: You lose the commit-by-commit story of how the config evolved. If you made 15 commits on WIP to get to the final state, only the final state ships — the 15 intermediate commits stay on the WIP branch and don't appear on main. For config files this is usually desirable; no one needs to see 15 iterations of a preset file.

**Warning**: `git checkout <branch> -- <path>` overwrites your working tree without asking. Make sure the PR branch doesn't have unrelated edits to the same path, or they'll be clobbered. `git status` after the command shows you exactly what changed.

### Strategy 2: Commit-based cherry-pick (preserves history)

**Best when**: Your WIP commits are meaningful on their own and you want each one to land on main as a separate commit. Rare for config work, but useful if (for example) you want to preserve a "before/after" for documentation.

**How it works**: `git cherry-pick <sha>` copies a single commit from another branch by creating a new commit with the same content on the current branch. The new commit has a different SHA but identical changes and original commit message.

```bash
# 1. Start from fresh main
git checkout main
git pull origin main

# 2. Create a feature branch
git checkout -b feature/lm-studio-config-stable

# 3. Find the commits you want from WIP (scoped to this client's path)
git log wip/client-config-iteration --oneline -- clients/lm-studio/

# Example output:
#   f3a21bc tweak(lm-studio): add Qwen3 4B Thinking preset
#   9de4f08 tweak(lm-studio): tune Research temperature to 0.3
#   1ba2c05 tweak(lm-studio): rewrite planner template

# 4. Cherry-pick them in chronological order (oldest first)
git cherry-pick 1ba2c05 9de4f08 f3a21bc

# 5. Resolve conflicts if any (see Troubleshooting below)

# 6. Push and open PR
git push -u origin feature/lm-studio-config-stable
gh pr create --base main --title "feat: stable LM Studio client configuration"
```

**Trade-off**: More commits to review, and potential for conflicts if the cherry-picked commits depend on each other in ways that don't survive reordering. Use strategy 1 unless you have a specific reason to preserve commit history.

## After the PR merges

Once your `feature/<client>-config` PR merges to main, you have two options for the WIP branch:

### Option A: Leave the WIP commits in place (simplest)

Do nothing. The WIP branch still contains all its original commits, including the ones that just landed on main through the PR. Git is smart about this — next time you rebase the WIP branch onto main, it detects the content-identical commits and silently drops them from the WIP branch.

```bash
git checkout wip/client-config-iteration
git fetch origin
git rebase origin/main
git push --force-with-lease
```

If the rebase detects that a WIP commit is content-identical to a commit already on main (which it will, for anything that got cherry-picked or path-checked), it drops the duplicate automatically. The WIP branch stays clean.

### Option B: Rebase WIP onto main immediately after each merge

Same commands as Option A, just run more eagerly. This keeps the WIP branch's `git log` short and avoids accumulating ghost commits that will get dropped later anyway.

```bash
git checkout wip/client-config-iteration
git fetch origin
git rebase origin/main
git push --force-with-lease
```

**Why `--force-with-lease` and not `--force`**: After a rebase, the branch history has been rewritten. You need to force-push because the remote branch no longer fast-forwards. `--force-with-lease` checks that the remote hasn't been updated since your last fetch — if someone else (or another machine) pushed to the branch, the push is rejected instead of silently overwriting their work. This is the safe default for force-pushing personal branches.

## Troubleshooting

### "I made a mess on wip — how do I throw it away?"

If your WIP branch has diverged in a way you don't want to keep:

```bash
# Nuclear option: reset WIP to match main
git checkout wip/client-config-iteration
git reset --hard origin/main
git push --force-with-lease
```

This discards **all local commits on the WIP branch** and restarts from current main. Make sure anything you want to keep has been promoted to a PR first.

### "I want to undo the last commit on wip without losing the changes"

```bash
git reset --soft HEAD~1
```

This removes the commit but keeps the changes staged so you can re-commit with a different message or split them into multiple commits.

### "Cherry-pick conflicts — what do I do?"

When `git cherry-pick` hits a conflict, git pauses and lets you resolve it manually:

```bash
# 1. Check which files have conflicts
git status

# 2. Edit files to resolve <<<<<<< ======= >>>>>>> markers
# (or use your editor's merge tool)

# 3. Mark resolved
git add <resolved-file>

# 4. Continue the cherry-pick
git cherry-pick --continue

# Or abort if it's too messy
git cherry-pick --abort
```

Cherry-pick conflicts are common when the WIP commits you're picking depend on intermediate commits you're not picking. If you keep hitting conflicts, switch to Strategy 1 (path-scoped checkout) — it sidesteps the issue entirely.

### "Path-scoped checkout took the wrong version"

`git checkout <branch> -- <path>` always takes the version from the **branch tip**, not from a specific commit. If the WIP branch has since advanced past the state you wanted, you need to specify a commit instead:

```bash
# Take files from a specific WIP commit instead of the tip
git checkout <sha> -- clients/lm-studio/
```

Find the right SHA with `git log wip/client-config-iteration -- clients/lm-studio/`.

### "I pushed a secret by accident"

GitHub push protection usually catches this (as happened with the HF token during PR #6). If a secret makes it through:

1. **Rotate the secret immediately** at the source (Hugging Face, OpenRouter, etc.)
2. Replace the value in the file with a placeholder (e.g., `YOUR_HF_TOKEN`)
3. Commit the fix and push

Do NOT try to rewrite history to remove the secret — once pushed, assume it's compromised. Rotation is the only real fix.

## Reference: common commands

| Task | Command |
| --- | --- |
| Switch to WIP | `git checkout wip/client-config-iteration` |
| See what's unique to WIP | `git log main..HEAD --oneline` |
| See commits touching one client | `git log HEAD --oneline -- clients/<name>/` |
| Diff WIP against main for one client | `git diff main..HEAD -- clients/<name>/` |
| Create a stable PR branch from main | `git checkout main && git pull && git checkout -b feature/<name>-config` |
| Path-scoped checkout from WIP | `git checkout wip/client-config-iteration -- clients/<name>/` |
| Cherry-pick a single commit | `git cherry-pick <sha>` |
| Cherry-pick a range | `git cherry-pick <sha1>..<sha2>` |
| Rebase WIP onto updated main | `git fetch origin && git rebase origin/main` |
| Force-push rebased WIP (safe) | `git push --force-with-lease` |
| Abort an in-progress cherry-pick | `git cherry-pick --abort` |
| Abort an in-progress rebase | `git rebase --abort` |

## See also

- [clients/README.md](README.md) — what lives in each client folder and how to set it up
- [docs/glossary.md](../docs/glossary.md) — definitions for bridge, proxy, client, privacy level
- [CHANGELOG.md](../CHANGELOG.md) — what's changed on main
