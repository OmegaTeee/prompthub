# git-pr-workflow

## Summary

This repo squash-merges PRs (commits land on `main` as a single `… (#N)` commit), and PRs are driven through `gh` non-interactively. That combination creates a handful of recurring gotchas — orphaned local commits, branches that won't delete, files that "vanish" on checkout, and `gh` prompts that block automation. None are bugs; they're consequences of squash + dirty-tree + `gh` that are worth knowing before they cost a debugging detour.

## Details

### Squash-merge breaks commit-identity assumptions

- **Feature commits never become ancestors of `main`.** A squash creates a *new* commit, so the branch's original SHAs are not in `main`'s history. Consequences:
  - `git branch -d <merged-branch>` **refuses** ("not fully merged") even though the PR landed. Use `git branch -D` once you've confirmed the squash commit `… (#N)` is in `main`.
  - `git log --oneline -- <file>` will **not** show your feature commit (its SHA was rewritten). Don't use it to confirm a merge.
- **Verify merged *content*, not commit identity.** The reliable check is `git diff main <branch-or-commit> -- <files>` → empty means `main` already contains those changes. Or grep `main`'s version directly (`git show main:path | grep …`).

### `gh pr merge --delete-branch` can orphan unpushed local commits

If you stacked extra commits on the *local* PR branch beyond what was pushed (e.g. a follow-up commit, or a `merge main` commit), `--delete-branch` deletes the branch and those commits become **dangling**. They are *not lost*: `git reflog` still references them (objects survive ~90 days), and `git branch <name> <sha>` re-anchors them instantly. Always verify the content reached `main` before assuming loss — in practice the work is usually already in the squash.

### Untracked / branch-local files "vanish" on checkout — expected

A freshly-created file (a new config, a new wiki page) committed to branch A **disappears from the working tree** when you `git checkout main`, because it isn't tracked on `main`. This is correct git behavior, not data loss — the file lives on branch A. The same is why `api-keys.json` and `schemathesis.toml` reverted to their `main` state during branch hops in earlier sessions.

### Stash-with-zero-overlap: work a different PR with a dirty tree

When the working tree holds unrelated in-flight changes and you need to touch a *different* PR branch:

```
git stash push -m "in-flight"     # tracked mods only; untracked files stay put
git checkout <other-branch>
# edit ONLY files that don't appear in the stash
git commit … && git push
git checkout <original-branch>
git stash pop                      # restores byte-for-byte
```

Safe **only** when your edits don't overlap any stashed file — then the pop never conflicts. If they overlap, expect a merge on pop. Confirm zero overlap first (compare your edit set against `git stash show --name-only`).

### `gh` non-interactive prompts

The repo has `gh config prefer_editor_prompt = enabled`, which makes `gh pr create` / `gh pr merge` try to open an editor and **fail in a non-tty context** ("not supported in non-tty mode"). Work around it per-operation: `gh config set prefer_editor_prompt disabled`, run the command with `--body-file` / `--title` (or `--subject`), then restore `enabled`. Reply to review comments with `gh api …/pulls/{n}/comments/{id}/replies`; resolve threads with the GraphQL `resolveReviewThread` mutation (map comment `databaseId` → thread node id first).

## Related

- [[schemathesis]] — the PR whose squash bundled an unpushed local fix; the `--delete-branch` orphaned-commit scare originated here.
- [[router-auth-tokens]] — landed via the api-keys PR that exercised the squash `-d`-vs-`-D` and config-reverts-on-checkout behaviors.

## Sources

- Session history (2026-06-02): three-PR sequence (#49 api-keys, #50 wiki, #51 schemathesis+500-fix) where these behaviors surfaced and were resolved.
- `gh` CLI docs — `pr merge --delete-branch`, `pr create --body-file`, `config set prefer_editor_prompt`.
